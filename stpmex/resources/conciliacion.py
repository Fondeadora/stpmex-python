import datetime as dt
from dataclasses import dataclass
from typing import Iterator, List, Optional

from ..auth import compute_signature
from ..types import TipoOperacion
from ..utils import strftime
from .base import Resource

EFWS_DEV_HOST = 'https://efws-dev.stpmex.com/efws/API/V2'
EFWS_PROD_HOST = 'https://prod.stpmex.com/efws/API/V2'


@dataclass
class Conciliacion(Resource):
    """
    Servicio para consultar las operaciones enviadas o recibidas del día o históricas.
    https://stpmex.zendesk.com/hc/es/articles/9192252705819-Conciliación-versión-2
    """

    _endpoint: str = '/conciliacion'

    def __post_init__(self):
        self.empresa: str
        self.firma: str
        self.page: int
        self.tipoOrden: str
        self.fechaOperacion: Optional[dt.date] = None

    @classmethod
    def consulta(
        cls, tipoOrden: TipoOperacion, fechaOperacion: Optional[dt.date] = None
    ) -> List['OrdenConsultada']:  # noqa: F821
        return [
            orden for page in cls._pages(tipoOrden, fechaOperacion) for orden in page
        ]

    @classmethod
    def _pages(
        cls, tipoOrden: TipoOperacion, fechaOperacion: Optional[dt.date] = None
    ) -> Iterator[List['OrdenConsultada']]:  # noqa: F821
        page = 0
        endpoint = cls._endpoint
        base_url = EFWS_PROD_HOST
        if cls._client.demo:
            base_url = EFWS_DEV_HOST

        while True:
            consulta = {
                'empresa': cls.empresa,
                'page': page,
                'tipoOrden': tipoOrden,
                'fechaOperacion': strftime(fechaOperacion) if fechaOperacion else '',
            }
            consulta['firma'] = cls._firma(consulta)

            resp = cls._client.post(endpoint, consulta, base_url=base_url)
            yield resp['datos']

            if resp['total'] < 1000 * (page + 1):
                break

            page += 1

    @classmethod
    def _firma(cls, consulta):
        joined = (
            f"||{cls.empresa}|"
            f"{consulta.get('tipoOrden').value}|"
            f"{consulta.get('fechaOperacion', '')}||"
        )
        return compute_signature(cls._client.pkey, joined)
