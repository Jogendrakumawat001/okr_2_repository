# -*- coding: utf-8 -*-
# Copyright (C) Gilliam Management Services and Information Systems, Ltd. (the owner of Bizzup), 2021, 2022, 2023, 2024, 2025
# All Rights Reserved to Gilliam Management Services and Information Systems, Ltd.
# Unauthorized copying, editing or printing of this file, in any way is strictly prohibited
# Proprietary and confidential for more information, please contact
# lg@bizzup.app
from odoo import models, _


class CrmLeadConfirmWizard(models.TransientModel):
    _name = 'crm.lead.confirm.wizard'
    _description = 'Confirm Lead Conversion'

    def action_confirm_conversion(self):
        """ #HT01500
        Prepare and return an action to convert a CRM lead to an opportunity partner.
        :return: Action dictionary for opening a new window to convert the lead.
        """
        active_id = self.env.context.get('active_id')
        return {
            'name': _('Convert to Opportunity'),
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead2opportunity.partner',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'crm.view_crm_lead2opportunity_partner').id,
            'target': 'new',
            'context': {
                'active_id': active_id,
                'active_ids': [active_id]},
        }