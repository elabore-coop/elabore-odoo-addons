# -*- coding: utf-8 -*-

from odoo import models, fields, _, api

class Lead(models.Model):
    _inherit="crm.lead"

    analytic_account = fields.Many2one('account.analytic.account', 'Analytic Account', required=False, index=True)
    plan_amount_with_coeff = fields.Float(related='analytic_account.plan_amount_with_coeff')
    
    def action_budget_forecast(self):
        if not self.analytic_account:
            message_id = self.env['budget.forecast.message.wizard'].create({'message': 'You must add an analytic account to build/access the budget forecast screen.'})
            return {
                'name': 'Missing Analytic Account',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'budget.forecast.message.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }
        return self.analytic_account.action_budget_forecast()