# -*- coding: utf-8 -*-

from odoo import models, fields, _, api
from odoo.exceptions import Warning

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    plan_amount_with_coeff = fields.Float(related='analytic_account_id.plan_amount_with_coeff')
    
    
    def action_budget_forecast(self):
        if not self.analytic_account_id:
            raise Warning(_('Please set the analytic account'))
        return self.analytic_account_id.action_budget_forecast()
    
    @api.returns('self', lambda value:value.id)
    def copy(self, default=None):
        record = super(SaleOrder, self).copy(default = default)
        if self.analytic_account_id.budget_forecast_ids:
            if self.name in self.analytic_account_id.name:
                name = self.analytic_account_id.name.replace(self.name, record.name)
            else:
                name = "%s: %s" % (self.analytic_account_id.name, record.name)
            record.analytic_account_id = self.analytic_account_id.copy(default = dict(name = name))
        return record    