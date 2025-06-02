# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app


{
    'name': 'Bizzup Purchase Serial Number',
    'version': '18.0.1.0.0',
    'description': """
        Adds lot/serial number field to purchase order lines '
       'and auto-assigns to stock move lines.
    """,
    'author': 'Softhealer Technologies',
    'website': 'www.bizzup.app',
    'depends': ['purchase_stock'],
    'data': [
        'data/serial_sequence.xml',
        'views/purchase_order_view.xml',
        'views/stock_move_line_view.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "bizzup_purchase_serial_number/static/src/views/**/*",
        ],
    },
    'installable': True,
    'application': False,
}