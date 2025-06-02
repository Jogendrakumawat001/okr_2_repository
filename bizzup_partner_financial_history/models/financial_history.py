# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential. For more information, please contact lg@bizzup.app

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FinancialHistory(models.Model):
    _name = "financial.history"
    _description = "Financial History"
    _order = "date desc"
    _rec_name = 'partner_id'

    invoice_id = fields.Many2one(
        "account.move", string="Invoice", required=True,
        domain=[("move_type", "=", "out_invoice")]
    )
    partner_id = fields.Many2one(related="invoice_id.partner_id",
                                 string="Contact")

    currency_id = fields.Many2one(related="invoice_id.currency_id")
    date = fields.Date(related="invoice_id.invoice_date", string="Date")
    amount_untaxed = fields.Monetary(
        related="invoice_id.amount_untaxed",
        string="Total before Tax",
        currency_field="currency_id",
    )
    amount_tax = fields.Monetary(
        related="invoice_id.amount_tax", string="Tax",
        currency_field="currency_id"
    )
    amount_total = fields.Monetary(
        related="invoice_id.amount_total", string="Amount",
        currency_field="currency_id"
    )

    @api.constrains('invoice_id')
    def _check_duplicate_invoice(self):
        """
        Ensure that no duplicate Financial History record is created for the same invoice.
        """
        for record in self:
            # Check if another financial history record already exists for the same invoice_id
            existing_history = self.search([
                ('invoice_id', '=', record.invoice_id.id),
                ('id', '!=', record.id)
            ])
            if existing_history:
                raise ValidationError(
                    _("A financial history record for this invoice already "
                      "exists.")
                )

    @api.model
    def sync_invoices(self):
        """
        Synchronize customer invoices into financial history records.

        This method finds all customer invoices (move_type = 'out_invoice') that are
        not yet linked to a financial history record, and creates corresponding
        entries in the financial.history model.

        """
        existing_invoice_ids = self.search([]).mapped("invoice_id").ids
        invoices = self.env["account.move"].search(
            [("move_type", "=", "out_invoice"),
             ("id", "not in", existing_invoice_ids)]
        )
        for invoice in invoices:
            self.create({"invoice_id": invoice.id})
