from enum import Enum
from typing import ClassVar, List

from pydantic.dataclasses import dataclass

from .base import Resource

EFWS_DEV_HOST = 'https://efws-dev.stpmex.com'
EFWS_PROD_HOST = 'https://prod.stpmex.com'


class EstadoBanco(str, Enum):
    desconectado = 'D'
    conectado = 'C'


@dataclass
class Banco(Resource):
    """
    Based on:
    https://stpmex.zendesk.com/hc/es/articles/4404221049243-Consulta-Instituciones
    """

    estado: EstadoBanco
    clave: str
    participante: str

    _endpoint: ClassVar[str] = '/efws/API/consultaInstituciones'

    @classmethod
    def consulta_instituciones(cls) -> List['Banco']:  # noqa: F821
        consulta = dict(
            empresa=cls.empresa,
            firma=cls._firma_consulta_instituciones_efws(),
        )
        base_url = EFWS_PROD_HOST
        if cls._client.demo:
            base_url = EFWS_DEV_HOST

        resp = cls._client.post(cls._endpoint, consulta, base_url=base_url)
        bancos = []
        for banco in resp['datos']:
            bancos.append(cls(**banco))
        return bancos
