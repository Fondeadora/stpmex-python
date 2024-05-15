import datetime as dt

import pytest

from stpmex import Client
from stpmex.types import TipoOperacion


@pytest.mark.vcr
def test_conciliacion_enviadas(client: Client):
    conciliaciones = client.conciliacion.consulta(TipoOperacion.enviada)

    assert len(conciliaciones) == 1
    for conciliacion in conciliaciones:
        assert conciliacion['institucionOperante'] == 90646


@pytest.mark.vcr
def test_conciliacion_recibidas(client: Client):
    conciliaciones = client.conciliacion.consulta(
        TipoOperacion.recibida, dt.date(2024, 5, 15)
    )

    assert len(conciliaciones) == 1
    for conciliacion in conciliaciones:
        assert conciliacion['institucionContraparte'] == 90646
