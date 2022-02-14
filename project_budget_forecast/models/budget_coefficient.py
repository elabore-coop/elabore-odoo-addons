# -*- coding: utf-8 -*-

from odoo import api, models, fields


class BudgetCoefficientModel(models.Model):
    _name = "budget.coefficient.model"
    description = "Coefficient Models for the order line price calculation"

    name = fields.Char(string="Name", required=True)
    coeff = fields.Float(string="Coefficient", required=True, default=0.00)
    note = fields.Text(string="Description")


class BudgetCoefficient(models.Model):
    _name = "budget.coefficient"
    _description = "Coefficients for the order line price calculation"

    name = fields.Char(string="Name", required=True)
    coeff = fields.Float(string="Coefficient", required=True, default=0.00)
    budget_forecast = fields.Many2one("account.analytic.account", string="Budget")
    note = fields.Text(string="Description")
