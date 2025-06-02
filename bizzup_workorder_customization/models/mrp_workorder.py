# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app

from odoo import models, fields, api


class MrpWorkorder(models.Model):
    """
    Inherit Manufacturing Work Order to include scrap quantity calculation
    and remaining on-hand quantity tracking.
    """

    _inherit = "mrp.workorder"

    scrap_qty = fields.Float(
        string="Scrap Quantity",
        compute="_compute_scrap_qty",
        store=True,
    )
    remaining_on_hand_qty = fields.Float(
        string="Remaining On-Hand QTY",
        compute="_compute_remaining_on_hand_qty",
    )

    @api.depends("scrap_ids.scrap_qty", "scrap_ids.state")
    def _compute_scrap_qty(self):
        """
        Compute total scrapped quantity related to the work order,
        considering only scraps with state 'done'.
        """
        for record in self:
            done_scraps = record.scrap_ids.filtered(lambda s: s.state == "done")
            record.scrap_qty = sum(done_scraps.mapped("scrap_qty"))

    @api.depends("scrap_qty")
    def _compute_remaining_on_hand_qty(self):
        """
        Compute remaining on-hand quantity when scrap quantity changes.
        """
        for record in self:
            total_on_hand_qty = sum(
                self.move_raw_ids.mapped("product_id.qty_available")
            )
            record.remaining_on_hand_qty = total_on_hand_qty
