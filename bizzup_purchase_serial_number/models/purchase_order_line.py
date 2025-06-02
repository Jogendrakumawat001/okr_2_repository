# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd.
# (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential. For more information, please contact lg@bizzup.app

from odoo import models, fields, api

class PurchaseOrderLine(models.Model):
    """
    Inherits from `purchase.order.line` to add a computed field for displaying the
    lot/serial name associated with the line's stock moves.
    """
    _inherit = 'purchase.order.line'

    lot_name = fields.Char(
        string="Lot/Serial Name",
        compute='_compute_lot_name',
        store=False,
        help="Displays the first available lot/serial name from the related stock move lines."
    )

    @api.depends('move_ids')
    def _compute_lot_name(self):
        """
        Computes the `lot_name` for the purchase order line by checking related stock move lines.
        If any move line has a `lot_name`, the first one (by ID) is shown.
        """
        for line in self:
            lot_name = ''
            move_lines = line.move_ids.mapped('move_line_ids').filtered(lambda l: l.lot_name)
            if move_lines:
                lot_name = move_lines.sorted(key=lambda l: l.id)[0].lot_name
            line.lot_name = lot_name
