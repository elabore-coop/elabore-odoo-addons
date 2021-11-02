# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    
    budget_forecast_ids = fields.One2many('budget.forecast', 'analytic_id', copy = True)
    project_section_budget_ids = fields.One2many('budget.forecast', 'analytic_id', domain = [('display_type','=', 'line_section')], copy = False)
    budget_coefficients_ids = fields.One2many('budget.coefficient', 'budget_forecast', copy=True)
    global_coeff = fields.Float('Global coefficient', compute = '_calc_global_coeff')
    plan_amount_without_coeff = fields.Float('Plan Amount without coeff', compute = '_calc_budget_amount')
    plan_amount_with_coeff = fields.Float('Plan Amount with coeff', compute = '_calc_budget_amount')
    actual_amount = fields.Float('Actual Amount', compute = '_calc_budget_amount')
    
    budget_category_ids = fields.Many2many('budget.forecast.category', compute = '_calc_budget_category_ids')
    
    display_actual_amounts = fields.Boolean(string='Display Actual Amounts', default=False)
    project_managers = fields.Many2many('res.users', string="Project managers",
                                        domain=lambda self: [('groups_id', 'in', self.env.ref('base.group_user').id)])


    def create(self, values):
        record = super(AccountAnalyticAccount, self).create(values)
        record.project_managers = self.env["res.users"].browse(self.env.user.id)
        return record

    @api.depends('budget_forecast_ids.plan_amount_without_coeff','budget_forecast_ids.plan_amount_with_coeff','budget_forecast_ids.actual_amount')
    def _calc_budget_amount(self):
        for record in self:
            line_ids = record.mapped('budget_forecast_ids').filtered(lambda line : (line.display_type == "line_section"))
            record.plan_amount_without_coeff = sum(line_ids.mapped('plan_amount_without_coeff'))
            record.plan_amount_with_coeff = sum(line_ids.mapped('plan_amount_with_coeff'))
            record.actual_amount = sum(line_ids.mapped('actual_amount'))

    def _calc_global_coeff(self):
        for record in self:
            line_ids = record.mapped('budget_coefficients_ids')
            record.global_coeff = sum(line_ids.mapped('coeff'))
    
    @api.depends('budget_forecast_ids')
    def _calc_budget_category_ids(self):
        for record in self:
            record.budget_category_ids = self.env['budget.forecast.category'].search([]).sorted()
    
    def action_budget_forecast(self):
        # Access only if the connected user is the project manager or an Odoo administrator
        if not (self.env.uid in self.project_managers.ids
                or self.env.user.has_group('base.group_system')):
            message_id = self.env['budget.forecast.message.wizard'].create({'message': 'You are not manager of this project.\nPlease contact the project manager or your Odoo administrator.'})
            return {
                'name': 'You are not the Project Manager',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'budget.forecast.message.wizard',
                'res_id': message_id.id,
                'target': 'new'
            }
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

    def displayActualAmounts(self):
        for record in self:
            if record.display_actual_amounts:
                record.display_actual_amounts = False
            else:
                record.display_actual_amounts = True

    def action_refresh(self):
        for record in self:
            line_ids = record.mapped('budget_forecast_ids')
            for line in line_ids:
                line.refresh()