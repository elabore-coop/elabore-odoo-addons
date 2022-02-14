# -*- coding: utf-8 -*-

from odoo import models, api


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    def _timesheet_preprocess(self, vals):
        vals = super(AccountAnalyticLine, self)._timesheet_preprocess(vals)
        if vals.get("so_line") and not vals.get("product_id"):
            so_line = self.env["sale.order.line"].browse(vals["so_line"])
            vals["product_id"] = so_line.product_id.id
        if vals.get("employee_id") and not vals.get("product_id"):
            employee = self.env["hr.employee"].browse(vals["employee_id"])
            vals["product_id"] = employee.timesheet_product_id.id
        return vals

    @api.model_create_multi
    @api.returns("self", lambda value: value.id)
    def create(self, vals_list):
        records = super(AccountAnalyticLine, self).create(vals_list)
        BudgetForecast = self.env["budget.forecast"].sudo()
        for record in records:
            if (
                record.amount < 0
                and record.product_id.budget_category_id
                and not BudgetForecast.search(
                    [
                        ("analytic_id", "=", record.account_id.id),
                        ("product_id", "=", record.product_id.id),
                    ],
                    limit=1,
                )
            ):
                BudgetForecast.create(
                    {
                        "description": record.product_id.name,
                        "analytic_id": record.account_id.id,
                        "product_id": record.product_id.id,
                        "main_category": record.product_id.budget_category_id.id,
                        "product_uom_id": self.product_id.uom_id,
                        "plan_price": self.product_id.standard_price,
                        "sequence": 9999,
                    }
                )

        return records
