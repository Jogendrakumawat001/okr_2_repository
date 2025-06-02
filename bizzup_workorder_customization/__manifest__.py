# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Work Order Customization",
    "description": """
    US HT01446
    This module customizes the Manufacturing Work Order (MRP) functionality by:
    - Calculating scrap quantity only for confirmed scraps (state 'done').
    - Tracking remaining on-hand quantity after accounting for scraps.
    - Enhancing work order tracking and material consumption efficiency.
    """,
    "version": "18.0.1.0.1",
    "license": "Other proprietary",
    "author": "Gilliam Management Services and Information Systems, Ltd.",
    "website": "https://bizzup.app",
    "depends": ["mrp"],
    "data": {
        "views/mrp_work_order_view.xml",
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}

