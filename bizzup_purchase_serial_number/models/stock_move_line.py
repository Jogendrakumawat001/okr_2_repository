# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd.
# (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential. For more information, please contact lg@bizzup.app

from odoo import models, api

class StockMoveLine(models.Model):
    """
    Inherits from `stock.move.line` to add a method that assigns serial numbers (lot names)
    using a sequence. This is typically used when generating serials manually through a wizard.
    """
    _inherit = 'stock.move.line'

    @api.model
    def action_assign_serial_numbers(self, record_ids):
        """
        Assigns serial numbers to the specified stock move line records using a predefined sequence.
        Only move lines that do not already have a `lot_name` will be updated.

        :param record_ids: List of stock.move.line record IDs to process.
        :return: True if operation completes successfully.
        """
        lines = self.browse(record_ids).sorted(key=lambda l: l.id)
        for line in lines:
            if not line.lot_name:
                serial = self.env['ir.sequence'].next_by_code(
                    'stock.move.line.lot.number')
                line.lot_name = serial
        return True
