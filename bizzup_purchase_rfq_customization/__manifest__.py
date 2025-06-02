# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Purchhase RFQ Customization",
    "description": """Customized purchase oder view""",
    "version": "18.0.2.0.4",
    "category": "",
    "license": "OPL-1",
    "author": "Gilliam Management Services and Information Systems, Ltd.",
    "website": "https://bizzup.app",
    "depends": ["purchase","bizzup_product_purchase_customization"],
    "data": [
        'report/purchase_quotation_template.xml',
        'views/purchase_order_form_views.xml',
    ],
    "demo": [],
    "installable": True,
    "application": False,
}
