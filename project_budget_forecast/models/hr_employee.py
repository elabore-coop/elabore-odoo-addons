from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    timesheet_product_id = fields.Many2one('product.product', string='Timesheet Product')