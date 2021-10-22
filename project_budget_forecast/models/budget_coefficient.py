# -*- coding: utf-8 -*-

from odoo import api, models, fields

class BudgetCoefficient(models.Model):
    _name = 'budget.coefficient'
    _description = 'Coefficients for the order line price calculation'

    name = fields.Text(string='Nom', required=True)
    coeff = fields.Float(string='Coefficient', required=True, default=0.00)
    budget_forecast = fields.Many2one('account.analytic.account', string="Budget", required=True)