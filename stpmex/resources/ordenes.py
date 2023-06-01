import datetime as dt
import random
import time
from dataclasses import field
from typing import ClassVar, List, Optional, Union

import clabe
from clabe.types import Clabe
from cuenca_validations.types import (
    PaymentCardNumber,
    StrictPositiveFloat,
    digits,
)
from pydantic import conint, constr, validator
from pydantic.dataclasses import dataclass

from ..auth import ORDEN_FIELDNAMES
from ..exc import NoOrdenesEncontradas
from ..types import (
    BeneficiarioClabe,
    MxPhoneNumber,
    Prioridad,
    TipoCuenta,
    TipoOperacion,
    truncated_str,
)
from ..utils import strftime
from .base import Resource

STP_BANK_CODE = 90646
EFWS_DEV_HOST = 'https://efws-dev.stpmex.com'


@dataclass
class Orden(Resource):
    """
    Based on:
    https://stpmex.zendesk.com/hc/es/articles/360002682851-RegistraOrden-Dispersi%C3%B3n-
    """

    _endpoint: ClassVar[str] = '/ordenPago'
    _firma_fieldnames: ClassVar[List[str]] = ORDEN_FIELDNAMES

    monto: StrictPositiveFloat
    conceptoPago: truncated_str(39)

    cuentaBeneficiario: Union[
        BeneficiarioClabe, PaymentCardNumber, MxPhoneNumber
    ]
    nombreBeneficiario: truncated_str(39)
    institucionContraparte: digits(5, 5)

    cuentaOrdenante: Clabe
    nombreOrdenante: Optional[truncated_str(39)] = None
    institucionOperante: digits(5, 5) = STP_BANK_CODE

    tipoCuentaBeneficiario: Optional[TipoCuenta] = None
    tipoCuentaOrdenante: TipoCuenta = TipoCuenta.clabe.value

    claveRastreo: truncated_str(29) = field(
        default_factory=lambda: f'CR{int(time.time())}'
    )
    referenciaNumerica: conint(gt=0, lt=10 ** 7) = field(
        default_factory=lambda: random.randint(10 ** 6, 10 ** 7)
    )
    rfcCurpBeneficiario: constr(max_length=18) = 'ND'
    rfcCurpOrdenante: Optional[constr(max_length=18)] = None

    prioridad: int = Prioridad.normal.value
    medioEntrega: int = 3
    tipoPago: int = 1
    topologia: str = 'T'
    iva: Optional[float] = None

    id: Optional[int] = None

    def __post_init__(self):
        cb = self.cuentaBeneficiario
        self.tipoCuentaBeneficiario = self.get_tipo_cuenta(cb)

    @classmethod
    def registra(cls, **kwargs) -> 'Orden':
        orden = cls(**kwargs)
        endpoint = orden._endpoint + '/registra'
        resp = orden._client.put(endpoint, orden.to_dict())
        orden.id = resp['id']
        return orden

    @staticmethod
    def get_tipo_cuenta(cuenta: str) -> Optional[TipoCuenta]:
        cuenta_len = len(cuenta)
        if cuenta_len == 18:
            tipo = TipoCuenta.clabe
        elif cuenta_len in {15, 16}:
            tipo = TipoCuenta.card
        elif cuenta_len == 10:
            tipo = TipoCuenta.phone_number
        else:
            tipo = None
        return tipo

    @validator('institucionContraparte')
    def _validate_institucion(cls, v: str) -> str:
        if v not in clabe.BANKS.values():
            raise ValueError(f'{v} no se corresponde a un banco')
        return v

    @classmethod
    def consulta_recibidas(
        cls, fecha_operacion: Optional[dt.date] = None
    ) -> List['OrdenConsultada']:  # noqa: F821
        """
        Consultar
        """
        return cls._consulta_fecha(TipoOperacion.recibida, fecha_operacion)

    @classmethod
    def consulta_enviadas(
        cls, fecha_operacion: Optional[dt.date] = None
    ) -> List['OrdenConsultada']:  # noqa: F821
        return cls._consulta_fecha(TipoOperacion.enviada, fecha_operacion)

    @classmethod
    def consulta_clave_rastreo(
        cls,
        claveRastreo: str,
        institucionOperante: Union[int, str],
        fechaOperacion: Optional[dt.date] = None,
    ) -> 'OrdenConsultada':  # noqa: F821
        """
        Consultar ordenes por clave rastreo. Exclude the fechaOperacion if
        looking up transactions from the same day or when the fechaOperacion is
        in the future, in the event of this function being called during
        non-banking hours (9am – 6pm) / days.

        Based on:
        https://stpmex.zendesk.com/hc/es/articles/360039782292-Consulta-Orden-Enviada-Por-Rastreo
        """
        institucionOperante = int(institucionOperante)
        if institucionOperante == STP_BANK_CODE:  # enviada
            consulta_method = cls._consulta_clave_rastreo_enviada

        else:  # recibida
            consulta_method = cls._consulta_clave_rastreo_recibida
        return consulta_method(
            claveRastreo, institucionOperante, fechaOperacion
        )

    @classmethod
    def _consulta_fecha(
        cls, tipo: TipoOperacion, fechaOperacion: Optional[dt.date] = None
    ) -> List['OrdenConsultada']:  # noqa: F821
        """
        Exclude the fechaOperacion if looking up transactions from the same
        day or when the fechaOperacion is in the future, in the event of this
        function being called during non-banking hours (9am – 6pm) / days.
        """
        endpoint = cls._endpoint + '/consOrdenesFech'
        consulta = dict(empresa=cls.empresa, estado=tipo)
        if fechaOperacion:
            consulta['fechaOperacion'] = strftime(fechaOperacion)
        consulta['firma'] = cls._firma_consulta(consulta)
        try:
            resp = cls._client.post(endpoint, consulta)
        except NoOrdenesEncontradas:
            ordenes = []
        else:
            ordenes = [
                cls._sanitize_consulta(orden) for orden in resp['lst'] if orden
            ]
        return ordenes

    @classmethod
    def _consulta_clave_rastreo_enviada(
        cls,
        claveRastreo: str,
        institucionOperante: int,
        fechaOperacion: Optional[dt.date] = None,
    ) -> 'OrdenConsultada':  # noqa: F821
        endpoint = cls._endpoint + '/consOrdEnvRastreo'
        consulta = dict(
            empresa=cls.empresa,
            claveRastreo=claveRastreo,
            institucionOperante=institucionOperante,
        )
        if fechaOperacion:
            consulta['fechaOperacion'] = strftime(fechaOperacion)
        consulta['firma'] = cls._firma_consulta(consulta)
        resp = cls._client.post(endpoint, consulta)['ordenPago']
        return cls._sanitize_consulta(resp)

    @classmethod
    def _consulta_clave_rastreo_recibida(
        cls,
        claveRastreo: str,
        institucionOperante: int,
        fechaOperacion: Optional[dt.date] = None,
    ) -> 'OrdenConsultada':  # noqa: F821
        recibidas = cls.consulta_recibidas(fechaOperacion)
        orden = None
        for o in recibidas:
            if o.claveRastreo == claveRastreo and institucionOperante in (
                o.institucionOperante,
                o.institucionContraparte,
            ):
                orden = o
                break
        if not orden:
            raise NoOrdenesEncontradas
        return orden


class OrdenV2(Resource):
    _endpoint: ClassVar[str] = '/efws/API/consultaOrden'

    @classmethod
    def consulta_clave_rastreo_enviada(
        cls, clave_rastreo: str, fecha_operacion: Optional[dt.date] = None
    ):
        return cls.consulta_orden(
            clave_rastreo, TipoOperacion.enviada, fecha_operacion
        )

    @classmethod
    def consulta_clave_rastreo_recibida(
        cls, clave_rastreo: str, fecha_operacion: Optional[dt.date] = None
    ):
        return cls.consulta_orden(
            clave_rastreo, TipoOperacion.recibida, fecha_operacion
        )

    @classmethod
    def consulta_orden(
        cls,
        clave_rastreo: str,
        tipo: TipoOperacion,
        fecha_operacion: Optional[dt.date] = None,
    ):
        consulta = dict(
            empresa=cls.empresa,
            claveRastreo=clave_rastreo,
            tipoOrden=tipo.value,
        )
        if fecha_operacion:
            consulta['fechaOperacion'] = strftime(fecha_operacion)

        consulta['firma'] = cls._firma_consulta_efws(consulta)
        base_url = EFWS_DEV_HOST if cls._client.demo else None

        resp = cls._client.post(cls._endpoint, consulta, base_url=base_url)
        return cls._sanitize_consulta(resp['respuesta'])
