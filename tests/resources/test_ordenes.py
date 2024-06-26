import datetime as dt
import time
from typing import Any, Dict
from unittest.mock import patch

import pytest
from cuenca_validations.typing import DictStrAny
from pydantic import ValidationError

from stpmex import Client
from stpmex.exc import BadRequestError, EmptyResultsError, NoOrdenesEncontradas
from stpmex.resources import Orden
from stpmex.types import TipoCuenta


@pytest.mark.vcr
def test_registra_orden(client: Client, orden_dict: Dict[str, Any]):
    orden_dict['claveRastreo'] = f'CR{int(time.time())}'
    orden = client.ordenes.registra(**orden_dict)
    assert isinstance(orden.id, int)


@pytest.mark.parametrize(
    'cuenta, tipo',
    [
        ('072691004495711499', TipoCuenta.clabe),
        ('4000000000000002', TipoCuenta.card),
        ('5512345678', TipoCuenta.phone_number),
        ('123', None),
    ],
)
def test_tipoCuentaBeneficiario(cuenta: str, tipo: TipoCuenta):
    assert Orden.get_tipo_cuenta(cuenta) == tipo


@pytest.mark.parametrize(
    'monto, msg',
    [
        (-1.3, 'ensure this value is greater than or equal to 0'),
        (1, 'value is not a valid float'),
    ],
)
def test_strict_pos_float(monto, msg: str, orden_dict: Dict[str, Any]):
    orden_dict['claveRastreo'] = f'CR{int(time.time())}'
    orden_dict['monto'] = monto

    with pytest.raises(ValidationError) as exc:
        Orden(**orden_dict)
    assert msg in str(exc.value)


def test_firma(client: Client, orden_dict: Dict[str, Any]):
    orden = Orden(**orden_dict)

    assert orden.firma == (
        'KDNKDVVuyNt9oTXPAlofGXGH5L5IH9PAzOsx0JZFtmGlU+10QRf2RHSg0OVCnYYpu5sC3'
        'DJ6vlXuYM40+uNw0tMc0y8Dv26uO8Vv2GhOhMqaGk72LwgwgmqVg17xzjgGbJHzAzMav3'
        'fx4/3No+mSnf7vxpe4ePf6yK1yU5U28L4='
    )


def test_firma_indirecta(client: Client, orden_indirecta_dict: Dict[str, Any]):
    orden = Orden(**orden_indirecta_dict)

    assert orden.firma == (
        'zjAbOxc0952Kk+wApZrlwykMVL9pZynECPOJrRj6gGa8lAI4Jn25paBLRkYS73Kd650ky'
        'SE1Nvrhxh4uFGeT9dI/nJ9e0uoc99Pwclbnik8bXPuQaEVqcAdoubrfLs3v+LYFO+Vmp8'
        'VSvhirr/XCGI999s5uCIS2IzNcfJSHfbg='
    )


@pytest.mark.vcr
def test_consulta_ordenes_enviadas(client):
    enviadas = client.ordenes.consulta_enviadas()
    assert len(enviadas) > 0


@pytest.mark.vcr
def test_consulta_ordenes_recibidas(client):
    recibidas = client.ordenes.consulta_recibidas()
    assert len(recibidas) > 0


@pytest.mark.vcr
def test_consulta_ordenes_enviadas_con_fecha(client):
    enviadas = client.ordenes.consulta_enviadas(dt.date(2020, 4, 20))
    assert len(enviadas) > 0


@pytest.mark.vcr
def test_consulta_ordenes_enviadas_con_fecha_sin_resultados(client):
    enviadas = client.ordenes.consulta_enviadas(dt.date(2021, 4, 20))
    assert len(enviadas) == 0


@pytest.mark.vcr
def test_consulta_orden_por_clave_rastreo(client):
    orden = client.ordenes.consulta_clave_rastreo(
        'CR1564969083', 90646, dt.date(2020, 4, 20)
    )
    assert orden.claveRastreo == 'CR1564969083'
    assert client.base_url == 'https://demo.stpmex.com:7024/speiws/rest'


@pytest.mark.vcr
def test_consulta_orden_por_clave_rastreo_efws(client, mocker):
    spy = mocker.spy(Client, 'post')
    orden = client.ordenes_v2.consulta_clave_rastreo(
        'CR1564969083', 90646, dt.date(2020, 4, 20)
    )
    args, kwargs = spy.call_args
    assert orden.claveRastreo == 'W1397800050926686208'
    assert kwargs['base_url'] == 'https://efws-dev.stpmex.com'


@pytest.mark.vcr
def test_consulta_orden_por_clave_rastreo_enviada_efws(client):
    orden = client.ordenes_v2._consulta_clave_rastreo_enviada(
        'CUENCA0000192923', dt.date(2023, 5, 18)
    )
    assert orden.claveRastreo == 'CUENCA0000192923'


@pytest.mark.vcr
def test_consulta_orden_recibida_por_clave_rastreo_efws(client):
    orden = client.ordenes_v2._consulta_clave_rastreo_recibida(
        'APZ450057199641', dt.date(2023, 5, 17)
    )
    assert orden.claveRastreo == 'APZ450057199641'
    assert orden.monto == 0.1


@pytest.mark.vcr
def test_consulta_orden_recibida_por_clave_rastreo_not_found_efws(client):
    with pytest.raises(EmptyResultsError) as exc:
        client.ordenes_v2._consulta_clave_rastreo_recibida(
            'APZ11111111111', dt.date(2023, 5, 17)
        )
    assert exc.value.estado == 6
    assert exc.value.mensaje == 'No se encontraron datos relacionados'


@pytest.mark.vcr
def test_consulta_orden_recibida_bad_request_efws(client):
    with pytest.raises(BadRequestError) as exc:
        client.ordenes_v2._consulta_clave_rastreo_recibida('')
    assert exc.value.estado == 2
    assert exc.value.mensaje == (
        '{claveRastreo=el campo clave de rastreo no puede venir vacio}'
    )


@pytest.mark.vcr
def test_consulta_orden_recibida_por_clave_rastreo_dia_operacion_efws(
    client,
):
    orden = client.ordenes_v2._consulta_clave_rastreo_recibida('TESTJSH5018035039')
    assert orden.claveRastreo == 'TESTJSH5018035039'
    assert orden.monto == 1.0


@pytest.mark.vcr
def test_consulta_orden_por_clave_rastreo_recibida(client):
    orden = client.ordenes.consulta_clave_rastreo(
        'CR1564969083', 40072, dt.date(2020, 4, 20)
    )
    assert orden.claveRastreo == 'CR1564969083'


@pytest.mark.vcr
def test_consulta_orden_sin_resultado(client):
    with pytest.raises(NoOrdenesEncontradas):
        client.ordenes.consulta_clave_rastreo(
            'does not exist', 90646, dt.date(2020, 4, 20)
        )


@pytest.mark.vcr
def test_consulta_orden_sin_resultado_recibida(client):
    with pytest.raises(NoOrdenesEncontradas):
        client.ordenes.consulta_clave_rastreo(
            'does not exist', 40072, dt.date(2020, 4, 20)
        )


@patch('stpmex.types.BLOCKED_INSTITUTIONS', {'90659'})
def test_institucion_bloqueada_no_permite_registrar_orden(
    client: Client, orden_dict: DictStrAny
):
    orden_dict['cuentaBeneficiario'] = '659802025000339321'
    expected_error_dict = dict(
        loc=('cuentaBeneficiario',),
        msg='Asp Integra Opc has been blocked by STP.',
        type='value_error.clabe.bank_code',
        ctx=dict(bank_name='Asp Integra Opc'),
    )
    with pytest.raises(ValidationError) as exc:
        client.ordenes.registra(**orden_dict)

    assert any(error == expected_error_dict for error in exc.value.errors())


@pytest.mark.vcr
def test_consulta_ordenes(client: Client):
    ordenes = client.ordenes_v2.consulta_ordenes(
        ['W1397800050926686208', '10454094'],
        90646,
    )

    assert len(ordenes) == 2
    assert ordenes[0].claveRastreo == 'W1397800050926686208'
    assert ordenes[1].claveRastreo == '10454094'


def test_consulta_ordenes_chunks(client: Client, mocker):
    clabes = [f'CLABE{i}' for i in range(301)]
    client_mock = mocker.patch.object(
        client,
        'post',
        return_value={'datos': [{'claveRastreo': 'CLABEXXX'}]},
    )
    ordenes = client.ordenes_v2.consulta_ordenes(
        clabes,
        90646,
    )

    assert client_mock.call_count == 4
    assert len(ordenes) == 4
    assert ordenes[0].claveRastreo == 'CLABEXXX'
