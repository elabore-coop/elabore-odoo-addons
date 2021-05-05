from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    dynamic_price = fields.Boolean("Use dynamic price ?")
