# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd.
# (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential. For more information, please contact lg@bizzup.app

from odoo import models, fields, api

class PurchaseOrder(models.Model):
    """
    Inherits from `purchase.order` to extend functionality related to stock pickings
    and to provide an action for assigning serial/lot numbers via a custom wizard.
    """
    _inherit = 'purchase.order'

    has_pickings = fields.Boolean(
        compute='_compute_has_pickings',
        string='Has Pickings',
        help='Indicates if this purchase order has any associated stock pickings.'
    )

    @api.depends('picking_ids')
    def _compute_has_pickings(self):
        """
        Computes whether the purchase order has related stock pickings.
        Sets the `has_pickings` Boolean field to True if any picking exists.
        """
        for order in self:
            order.has_pickings = bool(order.picking_ids)

    def action_open_serial_wizard(self):
        """
        Opens a popup window showing the stock move lines related to the purchase order's pickings.
        This allows the user to assign or edit lot/serial numbers manually.

        :return: Dictionary defining the action to open the tree view in a modal.
        """
        self.ensure_one()
        move_lines = self.picking_ids.mapped('move_line_ids')
        action = {
            'name': 'Assign Lot Serials',
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.line',
            'view_mode': 'list',
            'views': [(self.env.ref(
                'bizzup_purchase_serial_number'
                '.view_stock_move_line_serial_tree').id, 'list')],
            'domain': [('id', 'in', move_lines.ids)],
            'target': 'new',
        }
        return action
