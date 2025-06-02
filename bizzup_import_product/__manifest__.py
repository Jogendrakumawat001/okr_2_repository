# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

{
    "name": "Bizzup Product Import",
    "description": """
        Ticket : HT01634
        This module help to import product and lot from csv file
     """,
    "version": "18.0.1.0.0",
    "category": "",
    "license": "Other proprietary",
    "author": "Gilliam Management Services and Information Systems, Ltd.",
    "website": "www.bizzup.app",
    "depends": ["contacts", "sale_management", "purchase","stock"],
    "data": ["data/ir_cron_data.xml",
             "views/product_product_view.xml"],
    "installable": True,
    "application": False,
}
