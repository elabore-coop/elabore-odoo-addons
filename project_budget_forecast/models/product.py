from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    budget_category_id = fields.Many2one('budget.forecast.category', string='Budget Category', compute = '_calc_budget_category_id')
    budget_level = fields.Selection([('section', 'Section'), ('category', 'Category'), ('article', 'Article')], 
                                    string='Budget level', 
                                    required=True, 
                                    default='article')
    
    @api.depends('categ_id')
    def _calc_budget_category_id(self):
        for record in self:
            categ_id = record.categ_id
            budget_category_id = False
            while not budget_category_id and categ_id:
                budget_category_id = categ_id.budget_category_id
                categ_id = categ_id.parent_id
            record.budget_category_id = budget_category_id