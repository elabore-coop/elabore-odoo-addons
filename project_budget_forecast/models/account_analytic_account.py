from odoo import models, fields, api, _

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    
    budget_forecast_ids = fields.One2many('budget.forecast', 'analytic_id', copy = True)
    project_section_budget_ids = fields.One2many('budget.forecast', 'analytic_id', domain = [('budget_level','=', 'section')], copy = False)
        
    plan_amount = fields.Float('Plan Amount', compute = '_calc_budget_amount')
    actual_amount = fields.Float('Actual Amount', compute = '_calc_budget_amount')
    
    budget_category_ids = fields.Many2many('budget.forecast.category', compute = '_calc_budget_category_ids')
    
    @api.depends('budget_forecast_ids.plan_amount','budget_forecast_ids.actual_amount')
    def _calc_budget_amount(self):
        for record in self:
            line_ids = record.mapped('budget_forecast_ids').filtered(lambda line : not line.budget_level)
            record.plan_amount = sum(line_ids.mapped('plan_amount'))
            record.actual_amount = sum(line_ids.mapped('actual_amount'))
            
    
    @api.depends('budget_forecast_ids')
    def _calc_budget_category_ids(self):
        for record in self:
            record.budget_category_ids = record.mapped("budget_forecast_ids.category_id").sorted()
    
    def action_budget_forecast(self):
        return {
            'type' : 'ir.actions.act_window',
            'name' : _('Budget'),
            'res_model' : self._name,
            'res_id' : self.id,
            'view_mode' : 'form',
            'view_type' : 'form',
            'views' : [(self.env.ref('project_budget_forecast.view_analytic_budget_forecast').id, 'form')],
            'context' : {
                'budget_forecast' : True
                }    
            }            
        
        
    
    def name_get(self):
        if self._context.get('budget_forecast'):
            res = []
            for analytic in self:
                res.append((analytic.id, _('Budget')))
            return res
        return super(AccountAnalyticAccount, self).name_get()