import json
import os

import stpmex

client = stpmex.Client(
    empresa=os.environ['STP_COMPANY_NAME'],
    priv_key_passphrase=os.environ['STP_PRIVATE_KEY_PASSPHRASE'],
    priv_key=os.environ['STP_PRIVATE_KEY'],
    demo=True,
)


with open('scripts/cuenta.json') as cuenta_info:
    account = json.load(cuenta_info)
    stp_account = client.cuentas(**account)

with open('scripts/order.json') as order_info:
    order = json.load(order_info)
    stp_order = client.ordenes(**order)
