# -*- coding: utf-8 -*-

from odoo import models, fields, api

class BudgetForecast(models.Model):
    _name = 'budget.forecast'
    _description = _name
    _order = 'category_code,sequence,id'
    
    name = fields.Char('Description', required=True)    
    sequence = fields.Integer()
    analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account', required=True, ondelete='restrict', index=True)    
    category_id = fields.Many2one('budget.forecast.category', required = True)    
    category_code = fields.Char(related='category_id.code', store = True, readonly = True)
    
    budget_level = fields.Selection([('section', 'Section'), 
                                     ('category', 'Category'), 
                                     ('article', 'Article'), 
                                     ('note', 'Note')], 
                                     default=False)   
    display_type = fields.Selection([('line_section', "Section"),
                                     ('line_category', "Category"),
                                     ('line_note', "Note")],
                                     help="Technical field for UX purpose.") 
    
#    product_id = fields.Many2one('product.product', domain=[('budget_level', '=', budget_level)])
    product_id = fields.Many2one('product.product')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')    
    
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related="company_id.currency_id", string="Currency", readonly=True, store=True, compute_sudo=True)        
        
    plan_qty = fields.Float('Plan Quantity')
    plan_price = fields.Monetary('Plan Price', group_operator='avg')
    plan_amount_without_coeff = fields.Monetary('Plan Amount', compute = '_calc_plan_amount_without_coeff', store=True)
    plan_amount_with_coeff = fields.Monetary('Plan Amount with coeff', compute = '_calc_plan_amount_with_coeff', store=True)
    plan_amount_display = fields.Monetary('Plan Amount with coeff', store=True)
    
    analytic_line_ids = fields.Many2many('account.analytic.line', compute = '_calc_line_ids')
    actual_qty = fields.Float('Actual Quantity', compute = '_calc_actual', store=True, compute_sudo=True)
    actual_price = fields.Monetary('Actual Price', compute = '_calc_actual', store=True, compute_sudo=True, group_operator='avg')
    actual_amount = fields.Monetary('Actual Amount', compute = '_calc_actual', store=True, compute_sudo=True)
    actual_amount_display = fields.Monetary('Plan Amount with coeff', store=True)
    parent_id = fields.Many2one('budget.forecast', compute = '_calc_parent_id', store=True, compute_sudo=True)
    child_ids = fields.One2many('budget.forecast', 'parent_id')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and not self.name:
            self.name = self.product_id.name
        self.product_uom_id = self.product_id.uom_id
        self.plan_price = self.product_id.standard_price
    
    @api.depends('plan_qty', 'plan_price', 'child_ids')
    def _calc_plan_amount_without_coeff(self):
        for record in self:
            if record.child_ids:
                record.plan_amount_without_coeff = sum(record.mapped('child_ids.plan_amount_without_coeff'))
            else:
                record.plan_amount_without_coeff = record.plan_qty * record.plan_price

    @api.depends('plan_qty', 'plan_price', 'child_ids')
    def _calc_plan_amount_with_coeff(self):
        for record in self:
            record.plan_amount_with_coeff = record.plan_amount_without_coeff * (1 + record.analytic_id.global_coeff)

    @api.depends('child_ids')
    def _calc_plan_qty(self):
        for record in self:
            if record.child_ids:
                record.plan_qty = sum(record.mapped('child_ids.plan_qty'))

    @api.depends('child_ids')
    def _calc_plan_price(self):
        for record in self:
            if record.child_ids:
                lst = record.mapped('child_ids.plan_price')
                record.plan_price = lst and sum(lst) / len(lst)            
    
    @api.depends('analytic_id.budget_forecast_ids', 'child_ids', 'plan_qty', 'plan_price', 'analytic_id.global_coeff')
    def _calc_parent_id(self):
        for record in self:
            if record.display_type == 'line_section':
                record.parent_id = False
                continue
            found = False
            parent_id = False
            for line in record.analytic_id.budget_forecast_ids.sorted(reverse = True):
                if not found and line != record:
                    continue
                if line==record:
                    found = True
                    continue
                if (line.display_type == 'line_article') or (line.display_type == 'line_note'):
                    continue
                elif line.display_type == 'line_category':
                    if record.display_type == 'line_article':
                        parent_id = line
                        break
                    else:
                        continue
                elif line.display_type == 'line_section':
                    parent_id = line
                    break          
            record.parent_id = parent_id
                
    @api.depends('analytic_id', 'child_ids')
    def _calc_line_ids(self):
        for record in self:
            if record.child_ids:
                record.analytic_line_ids = record.mapped('child_ids.analytic_line_ids')
                continue
            domain = [('account_id', '=', record.analytic_id.id), ('company_id', '=', record.company_id.id), ('product_id', '=', record.product_id.id)]
            record.analytic_line_ids = self.env['account.analytic.line'].search(domain)    
    
    @api.depends('analytic_id.line_ids.amount')
    def _calc_actual(self):
        for record in self:
            child_actual_qty = 0
            child_actual_amount = 0
            if record.child_ids:
                child_actual_qty = sum(record.mapped('child_ids.actual_qty'))
                child_actual_amount = sum(record.mapped('child_ids.actual_amount'))
            line_ids = record.analytic_line_ids
            record.actual_qty = abs(sum(line_ids.mapped('unit_amount'))) + child_actual_qty
            record.actual_amount = -sum(line_ids.mapped('amount')) + child_actual_amount
            record.actual_price = abs(record.actual_qty and record.actual_amount / record.actual_qty)
    
    def _calc_plan(self):
        self._calc_plan_amount_without_coeff()
        self._calc_plan_amount_with_coeff()
        self._calc_plan_qty()
        self._calc_plan_price()                    

    def _update_parent_plan(self):
        self.exists().mapped('parent_id')._calc_plan()
                        
    @api.model_create_multi
    @api.returns('self', lambda value:value.id)
    def create(self, vals_list):
        records = super(BudgetForecast, self).create(vals_list)
        records._update_parent_plan()
        return records

    def write(self, vals):
        res= super(BudgetForecast, self).write(vals)
        self._update_parent_plan()
        return res

    def unlink(self):
        parent_ids = self.mapped('parent_id')
        
        res= super(BudgetForecast, self).unlink()
        
        parent_ids.exists()._calc_plan()
        return res
        
        