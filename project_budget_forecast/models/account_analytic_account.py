# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    budget_forecast_ids = fields.One2many("budget.forecast", "analytic_id", copy=True)
    project_section_budget_ids = fields.One2many(
        "budget.forecast",
        "analytic_id",
        domain=[
            ("display_type", "in", ["line_section", "line_subsection"]),
            ("is_summary", "=", True),
        ],
        copy=False,
    )
    budget_coefficients_ids = fields.One2many(
        "budget.coefficient",
        "budget_forecast",
        copy=True,
    )
    global_coeff = fields.Float("Global coefficient", compute="_calc_global_coeff")
    plan_amount_without_coeff = fields.Float(
        "Plan Amount without coeff", compute="_calc_budget_amount"
    )
    plan_amount_with_coeff = fields.Float(
        "Plan Amount with coeff", compute="_calc_budget_amount"
    )
    actual_amount = fields.Float("Actual Amount", compute="_calc_budget_amount")
    diff_amount = fields.Float("Diff Amount", compute="_calc_budget_amount")
    budget_category_ids = fields.Many2many(
        "budget.forecast.category", compute="_calc_budget_category_ids"
    )

    display_actual_amounts = fields.Boolean(
        string="Display Actual Amounts", default=False
    )
    project_managers = fields.Many2many(
        "res.users",
        string="Project managers",
        domain=lambda self: [("groups_id", "in", self.env.ref("base.group_user").id)],
    )
    opportunity = fields.Many2one(
        "crm.lead",
        string="Opportunity",
        compute="_compute_opportunity",
    )

    def default_budget_coefficients_ids(self):
        for coeff in self.budget_coefficients_ids:
            coeff.unlink()
        coeff_models = self.env["budget.coefficient.model"].search([])
        for model in coeff_models:
            vals = {
                "name": model.name,
                "coeff": model.coeff,
                "note": model.note,
                "budget_forecast": self.id,
            }
            self.env["budget.coefficient"].create(vals)

    def _compute_opportunity(self):
        lead = self.env["crm.lead"].search(
            [("analytic_account", "=", self.id)], limit=1
        )
        if lead:
            self.opportunity = lead.id

    @api.model
    def create(self, values):
        record = super(AccountAnalyticAccount, self).create(values)
        if not record.project_managers:
            record.project_managers = self.env["res.users"].browse(self.env.user.id)
        record.default_budget_coefficients_ids()
        return record

    @api.depends(
        "budget_forecast_ids.plan_amount_without_coeff",
        "budget_forecast_ids.plan_amount_with_coeff",
        "budget_forecast_ids.actual_amount",
    )
    def _calc_budget_amount(self):
        for record in self:
            line_ids = record.mapped("budget_forecast_ids").filtered(
                lambda line: (line.display_type == "line_section")
                and (line.is_summary == True)
            )
            record.plan_amount_without_coeff = sum(
                line_ids.mapped("plan_amount_without_coeff")
            )
            record.plan_amount_with_coeff = sum(
                line_ids.mapped("plan_amount_with_coeff")
            )
            record.actual_amount = sum(line_ids.mapped("actual_amount"))
            record.diff_amount = record.plan_amount_with_coeff - record.actual_amount

    def _calc_global_coeff(self):
        for record in self:
            line_ids = record.mapped("budget_coefficients_ids")
            record.global_coeff = sum(line_ids.mapped("coeff"))

    @api.depends("budget_forecast_ids")
    def _calc_budget_category_ids(self):
        for record in self:
            record.budget_category_ids = (
                self.env["budget.forecast.category"].search([]).sorted()
            )

    def action_budget_forecast(self):
        # Access only if the connected user is the project manager or an Odoo administrator
        if not (
            self.env.uid in self.project_managers.ids
            or self.env.user.has_group("base.group_system")
        ):
            raise UserError(
                _(
                    "You are not manager of this project.\nPlease contact the project manager or your Odoo administrator."
                )
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Budget"),
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "view_type": "form",
            "views": [
                (
                    self.env.ref(
                        "project_budget_forecast.view_analytic_budget_forecast"
                    ).id,
                    "form",
                )
            ],
            "context": {"budget_forecast": True},
        }

    def name_get(self):
        if self._context.get("budget_forecast"):
            res = []
            for analytic in self:
                res.append((analytic.id, _("Budget")))
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
            line_ids = record.mapped("budget_forecast_ids")
            for line in line_ids:
                line.refresh()

    def action_create_quotation(self):
        quotation = self.env["sale.order"].create(
            {
                "company_id": self.company_id.id,
                "partner_id": self.env.user.partner_id.id,
            }
        )
        for section in self.project_section_budget_ids.filtered(
            lambda s: s.display_type == "line_section"
        ):
            values = {
                "order_id": quotation.id,
                "product_id": section.product_id.id,
                "name": section.product_id.name,
                "product_uom": section.product_uom_id.id,
                "product_uom_qty": 1.0,
                "price_unit": section.plan_amount_with_coeff,
            }
            self.env["sale.order.line"].create(values)
        quotation.analytic_account_id = self.id
        quotation.opportunity_id = self.opportunity.id
        return {
            "type": "ir.actions.act_window",
            "name": _("Quotation"),
            "res_model": "sale.order",
            "res_id": quotation.id,
            "view_mode": "form",
            "view_type": "form",
            "views": [
                (
                    self.env.ref("sale.view_order_form").id,
                    "form",
                )
            ],
        }
