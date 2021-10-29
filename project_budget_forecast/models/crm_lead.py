# -*- coding: utf-8 -*-

from odoo import models, fields, _, api

class Lead(models.Model):
    _inherit="crm.lead"

    analytic_account = fields.Many2one('account.analytic.account', 'Analytic Account', required=False, index=True)
    plan_amount_with_coeff = fields.Float(related='analytic_account.plan_amount_with_coeff')
    
    def action_budget_forecast(self):
        if not self.analytic_account:
            raise Warning(_('Please set the analytic account'))
        return self.analytic_account.action_budget_forecast()