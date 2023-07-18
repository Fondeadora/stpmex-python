import pytest
from clabe import generate_new_clabes

from stpmex.exc import DuplicatedAccount
from stpmex.resources import CuentaFisica, CuentaMoral


@pytest.mark.vcr
def test_alta_cuenta(client, persona_fisica_dict):
    cuenta = client.cuentas.alta(**persona_fisica_dict)
    assert cuenta


@pytest.mark.vcr
def test_baja_cuenta(client, cuenta_persona_fisica):
    assert cuenta_persona_fisica.baja()


@pytest.mark.vcr
@pytest.mark.parametrize('num_cuentas', [95])
def test_alta_lote(client, persona_fisica_dict, num_cuentas):
    del persona_fisica_dict['cuenta']
    clabes = generate_new_clabes(num_cuentas, '6461801570')

    lote = []
    for clabe in clabes:
        cuenta = CuentaFisica(**persona_fisica_dict, cuenta=clabe)
        lote.append(cuenta)
    resp = client.cuentas.alta_lote(lote)
    assert list(resp.keys()) == clabes
    assert all(r['id'] == 0 for r in resp.values())
    assert all(
        r['descripcion'] == 'Cuenta en revisión.' for r in resp.values()
    )
    for cuenta in lote:
        cuenta.baja()


def test_cuenta_nombre_apellidos_correctos(cuenta_persona_fisica):
    assert cuenta_persona_fisica.nombre == 'EDUARDO MARCO'
    assert cuenta_persona_fisica.apellidoMaterno == 'HERNANDEZ MUNOZ'
    assert cuenta_persona_fisica.apellidoPaterno == 'SALVADOR'


@pytest.mark.vcr
def test_alta_cuenta_persona_moral(client, persona_moral_dict):
    cuenta = client.cuentas_morales.alta(**persona_moral_dict)
    assert cuenta.nombre == persona_moral_dict['nombre'].upper()
    assert all(
        [
            getattr(cuenta, k) == v
            for k, v in persona_moral_dict.items()
            if k != 'nombre'
        ]
    )

    with pytest.raises(DuplicatedAccount):
        client.cuentas_morales.alta(**persona_moral_dict)


@pytest.mark.vcr
def test_alta_cuenta_persona_moral_multiples_clabes(
    client, persona_moral_dict
):
    clabes = ['646180157019963860', '646180157034931699', '646180157017954923']
    for clabe in clabes:
        persona_moral_dict['cuenta'] = clabe
        cuenta = client.cuentas_morales.alta(**persona_moral_dict)
        assert cuenta.nombre == persona_moral_dict['nombre'].upper()
        assert all(
            [
                getattr(cuenta, k) == v
                for k, v in persona_moral_dict.items()
                if k != 'nombre'
            ]
        )


@pytest.mark.vcr
def test_alta_lote_persona_moral(client, persona_moral_dict):
    del persona_moral_dict['cuenta']
    clabes = generate_new_clabes(10, '64618015701')

    lote = []
    for clabe in clabes:
        cuenta = CuentaMoral(**persona_moral_dict, cuenta=clabe)
        lote.append(cuenta)
    resp = client.cuentas_morales.alta_lote(lote)
    assert list(resp.keys()) == clabes
    assert all(r['id'] == 0 for r in resp.values())
    assert all(
        r['descripcion'] == 'Cuenta en revisión.' for r in resp.values()
    )
