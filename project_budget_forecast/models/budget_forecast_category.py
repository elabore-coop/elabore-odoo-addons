# -*- coding: utf-8 -*-

from odoo import models, fields, api
import re

def normilize(*names):
    name = ' '.join(names)
    return re.sub('\W',' ', name.lower()).strip().replace(' ', '_')    

def remove_unchange(vals, record):
    for fname in list(vals):
        value = vals[fname]
        field = record._fields[fname]
        value = field.convert_to_cache(value, record, validate=False)
        value = field.convert_to_record(value, record)
        if record[fname] == value:
            vals.pop(fname)
            
_view_arch = """
<data>
<notebook> 
    <page name="%(name)s" string="%(name)s" >
        <field name="%(field_name)s" widget="section_category_and_note_one2many" mode="tree" nolabel="1">
            <tree editable="bottom">            
                <control>
                    <create string="Add a section" context="{'default_display_type': 'line_section'}" />
                    <create string="Add a sub-section" context="{'default_display_type': 'line_subsection'}" />
                    <create string="Add an article" context="{'default_display_type': 'line_article', 'default_main_category' : %(id)d}" />
                    <create string="Add a note" context="{'default_display_type': 'line_note', 'default_main_category' : %(id)d}" />
                </control>                
                <field name="sequence" widget="handle" />  
                <field name="main_category" invisible="1" optional="hide" />
                <field name="parent_id" optional="hide" />
                <field name="display_type" invisible="1" />
                <field name="product_id" />
                <field name="description" />
                <field name="product_uom_id" optional="hide"/>
                <field name="plan_price"/>
                <field name="actual_price" attrs="{'column_invisible' : [('parent.display_actual_amounts', '=', False)]}"/>
                <field name="plan_qty"/>
                <field name="actual_qty" attrs="{'column_invisible' : [('parent.display_actual_amounts', '=', False)]}"/>
                <field name="plan_amount_without_coeff" string="Plan Amount before Coeff"/>
                <field name="plan_amount_with_coeff" string="Plan Amount after Coeff"/>
                <field name="actual_amount" string="Actual Amount" attrs="{'column_invisible' : [('parent.display_actual_amounts', '=', False)]}"/>                                    
            </tree>
        </field>
    </page>
</notebook>
</data>
"""            
            
class BudgetForecastCategory(models.Model):
    _name = 'budget.forecast.category'
    _description = _name
    _order = 'sequence,id'
    
    sequence = fields.Integer()
    name = fields.Char(required = True)
    code = fields.Char(required = True)
    
    field_id = fields.Many2one('ir.model.fields', readonly = True)
    field_name = fields.Char(related='field_id.name', readonly = True)
    view_id = fields.Many2one('ir.ui.view', readonly = True)        
    
    _sql_constraints = [
        ('uk_name', 'unique(name)', 'Name must be unique!'),
        ('uk_code', 'unique(code)', 'Code must be unique!')
        ]

    
    def _create_field(self):
        if self.field_id:
            if self.field_id.field_description != self.name:
                self.field_id.field_description = self.name
            return
        self = self.sudo()
        vals = {            
            'field_description' : self.name,
            'name' : 'x_%s_budget_forecast_ids' % (normilize(self.code)),
            'model_id' : self.env['ir.model']._get_id('account.analytic.account'),
            'ttype':'one2many',
            'relation':'budget.forecast',
            'relation_field': 'analytic_id',
            'domain': "['|',('main_category.code','=','%s'),('display_type','in',['line_section','line_subsection'])]" %(self.code),
            'copied' : False                      
            }
        self.field_id=self.env['ir.model.fields'].create(vals)
    
    
    def _get_view_arch(self):
        vals, = self.read([], load = False)
        return _view_arch % vals
        
    
    def _create_view(self):
        self = self.sudo()
        inherit_id = self.env.ref('project_budget_forecast.view_analytic_budget_forecast')
        vals = {
            'arch' : self._get_view_arch(),
            'priority' : self.search([]).ids.index(self.id) + 1,
            'inherit_id' : inherit_id.id,
            'type' : inherit_id.type,
            'model' : inherit_id.model,
            'name' : '%s.%s' % (inherit_id.name, self.code)
            }
        
        if self.view_id:
            remove_unchange(vals, self.view_id)
            self.view_id.write(vals)
        else:
            self.view_id = self.env['ir.ui.view'].create(vals)
    
    @api.model
    def _update_views(self):        
        for record in self.search([]):
            record._create_field()
            record._create_view()
            
            
    
    def unlink(self):
        view_ids = self.mapped('view_id')
        field_ids = self.mapped('field_id')
        
        res = super(BudgetForecastCategory, self).unlink()
        
        view_ids.unlink()
        field_ids.unlink()
        
        self.sudo()._update_views()
        
        return res
    
    
    @api.model_create_multi
    @api.returns('self', lambda value:value.id)
    def create(self, vals_list):
        records = super(BudgetForecastCategory, self).create(vals_list)
        self.sudo()._update_views()
        return records
        
        
    def write(self, vals):
        res = super(BudgetForecastCategory, self).write(vals)
        self.sudo()._update_views()
        return res