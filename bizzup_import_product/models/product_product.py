# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'


    def init(self):
        return False


    status = fields.Selection(
        [('returned', 'Returned'), ('sold', 'Sold'),
         ('other', 'Other'), ('personal use', 'Personal Use'),
         ('wish list', 'Wish List'), ('order reserved', 'Order Reserved'),
         ('inventory reserved', 'Inventory Reserved'), ('barter', 'Barter'),
         ('missing', 'Missing'), ('in stock', 'In Stock')
         ],
        string='Status'
    )
    source = fields.Selection([
        ('eu', 'EU'),
        ('br', 'BR'),
        ('na', 'N/A'),
    ], string='Source', default='na')
    date_order = fields.Date(string='Date Ordered')
    arrival_date = fields.Date(string='Arrival Date')
    sold_date = fields.Date(string='Sold Date')
