from stpmex.auth import (
    CUENTA_FIELDNAMES,
    ORDEN_FIELDNAMES,
    compute_signature,
    join_fields,
)


def test_join_fields_for_orden(orden):
    joined = (
        '||40072|TAMIZI|||CR1564969083|90646|1.20|1|40||646180110400000007|'
        '|40|Ricardo Sanchez|072691004495711499|ND||||||Prueba||||||5273144|'
        '|T||3|0||||||'
    )
    assert join_fields(orden, ORDEN_FIELDNAMES) == joined


def test_join_fields_for_orden_indirecta(orden_indirecta):
    joined = (
        '||40072|TAMIZI|||CR1564969083|90646|1.20|1|40||646180110400000007|'
        '|40|Ricardo Sanchez|072691004495711499|ND||||||Prueba||||||5273144|'
        '|T||3|0||AMU|646180157099999993|WDCT680526LI0||'
    )
    assert join_fields(orden_indirecta, ORDEN_FIELDNAMES) == joined


def test_join_fields_for_cuenta(cuenta_persona_fisica):
    cuenta_persona_fisica.cuenta = '646180157099999993'
    joined = '||TAMIZI|646180157099999993|SAHE800416HDFABC01||'
    assert join_fields(cuenta_persona_fisica, CUENTA_FIELDNAMES) == joined


def test_compute_signature(client, orden):
    firma = (
        'CLcckJl2Xv775aKhYu4NZoU5fRXMtIyuZjoG+CXvpxwETj8PixZrTqf3Ckzes+3QeFSUK/'
        'ilGMnxH5Btry7sSV7UyKUXcQ6j8d2VxNJdkPmlXWg0QMAD+h4MLym70P/sBV+2/5NT0wvvZ'
        'yn6y7wKO1VlHij9UwL8JM9rVDYOjBs='
    )
    sig = compute_signature(client.pkey, join_fields(orden, ORDEN_FIELDNAMES))
    assert sig == firma
