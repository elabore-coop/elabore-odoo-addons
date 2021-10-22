# -*- coding: utf-8 -*-

from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = "product.category"
    
    budget_category_id = fields.Many2one('budget.forecast.category', string='Budget Category')    