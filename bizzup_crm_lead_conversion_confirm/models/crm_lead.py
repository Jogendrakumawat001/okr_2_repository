# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app
from odoo import models, _


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def action_open_conversion_wizard(self):
        """ #HT01500
        Opens a confirmation wizard for lead conversion.
        :return: An action dictionary to display the confirmation wizard in
        a popup.
        """
        return {
            'name': _('Confirm Lead Conversion'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead.confirm.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'bizzup_crm_lead_conversion_confirm.view_crm_lead_confirm_wizard').id,
            'target': 'new',
        }