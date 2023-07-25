import pytest

from stpmex.resources import Banco


@pytest.mark.vcr
def test_consulta_instituciones(client):
    bancos = client.bancos.consulta_instituciones()
    for banco in bancos:
        assert isinstance(banco, Banco)
    assert len(bancos) == 2
