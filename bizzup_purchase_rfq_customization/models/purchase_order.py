# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    total_price = fields.Monetary('Total Price', currency_field='currency_id')

    state = fields.Selection(
        selection_add=[('on_hold', "On Hold")],
        ondelete={'on_hold': 'set default'}
    )

    def _sync_total_price_line(self):
        """Ensure a line named 'Total Price Line' exists and reflects the total_price field."""
        for order in self:
            if order.total_price:
                existing_line = order.order_line.filtered(lambda l: l.name == 'Total Price Line')
                tax = self.env.ref('account.1_purchase_tax_template')
                vals = {
                    'name': 'Total Price Line',
                    'price_unit': order.total_price,
                    'product_qty': 1.0,
                    'date_planned':order.create_date,
                    'product_uom': self.env.ref('uom.product_uom_unit').id,
                    'taxes_id': [(6, 0, [tax.id])] if tax else False,
                }
                if existing_line:
                    vals = {
                        'date_planned': order.create_date,
                        'price_unit': order.total_price,
                    }
                    existing_line.write(vals)
                else:
                    self.env['purchase.order.line'].create({
                        **vals,
                        'order_id': order.id,
                    })

    @api.model
    def create(self, vals):
        order = super().create(vals)
        order._sync_total_price_line()
        return order

    def write(self, vals):

        res = super().write(vals)
        # Sync total price line
        if 'total_price' in vals:
            self._sync_total_price_line()

        return res

    def button_cancel(self):
        for order in self:
            if order.create_uid and order.create_uid.partner_id.email:
                email_values = {
                    'email_to': order.create_uid.partner_id.email,
                    'subject': f"RFQ {order.name} Cancelled",
                    'body_html': f"""
                        <p>Dear {order.create_uid.name},</p>
                        <p>The RFQ <strong>{order.name}</strong> has been <span style="color:red;"><strong>cancelled</strong></span>.</p>
                    """,
                }
                self.env['mail.mail'].create(email_values).send()

        return super().button_cancel()

    def action_on_hold_stage(self):
        for order in self:
            order.state = 'on_hold'
            if order.user_id and order.user_id.partner_id.email:
                email_values = {
                    'email_to': order.user_id.partner_id.email,
                    'subject': f"Purchase Order {order.name} Moved to On Hold",
                    'body_html': f"""
                        <p>Dear {order.user_id.name},</p>
                        <p>The purchase order <strong>{order.name}</strong> has been moved to <strong>On Hold</strong>.</p>
                    """,
                }
                self.env['mail.mail'].create(email_values).send()
