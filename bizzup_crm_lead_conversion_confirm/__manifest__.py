# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app
{
    'name': 'CRM Lead Conversion Confirmation',
    'version': '18.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Adds a confirmation step before converting leads to opportunities.',
    'license': 'Other proprietary',
    'author': 'Gilliam Management Services and Information Systems, Ltd.',
    'website': 'www.bizzup.app',
    'depends': ['crm'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/crm_lead_confirm_wizard.xml',
        'views/crm_lead_form.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
