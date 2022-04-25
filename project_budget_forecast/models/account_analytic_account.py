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
    total_expenses = fields.Float("Total expenses", compute="_calc_budget_amount")
    remaining_budget = fields.Float("Remaining budget", compute="_calc_budget_amount")
    total_incomes = fields.Float("Total incomes", compute="_calc_budget_amount")
    project_balance = fields.Float("Project Balance", compute="_calc_budget_amount")
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
            # Planned amounts
            record.plan_amount_without_coeff = sum(
                line_ids.mapped("plan_amount_without_coeff")
            )
            record.plan_amount_with_coeff = sum(
                line_ids.mapped("plan_amount_with_coeff")
            )
            # Expenses
            record.total_expenses = sum(line_ids.mapped("actual_amount"))
            record.remaining_budget = (
                record.plan_amount_with_coeff - record.total_expenses
            )
            # Incomes
            record.total_incomes = 0
            domain = [
                ("analytic_account_id", "=", record.id),
                ("parent_state", "in", ["draft", "posted"]),
                ("move_id.type", "in", ["out_invoice", "out_refund"]),
            ]
            draft_invoice_lines = self.env["account.move.line"].search(domain)
            for invoice_line in draft_invoice_lines:
                if invoice_line.move_id.type == "out_invoice":
                    record.total_incomes = (
                        record.total_incomes + invoice_line.price_subtotal
                    )
                elif invoice_line.move_id.type == "out_refund":
                    record.total_incomes = (
                        record.total_incomes - invoice_line.price_subtotal
                    )
            # Balance
            record.project_balance = record.total_incomes - record.total_expenses

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

    def _update_summary(self):
        for record in self:
            summary_line_ids = (
                record.mapped("budget_forecast_ids")
                .filtered(lambda x: x.is_summary)
                .sorted(key=lambda r: r.sequence, reverse=True)
            )
            for summary_line in summary_line_ids:
                # find corresponding category section/sub_section lines
                lines = record.mapped("budget_forecast_ids").filtered(
                    lambda x: (
                        (not x.is_summary) and (x.summary_id.id == summary_line.id)
                    )
                )
                # Calculate the total amounts
                summary_line.plan_amount_without_coeff = 0
                summary_line.plan_amount_with_coeff = 0
                summary_line.actual_amount = 0
                for line in lines:
                    summary_line.plan_amount_without_coeff += (
                        line.plan_amount_without_coeff
                    )
                    summary_line.plan_amount_with_coeff += line.plan_amount_with_coeff
                    summary_line.actual_amount += line.actual_amount

    def action_refresh(self):
        for record in self:
            line_ids = record.mapped("budget_forecast_ids").sorted(
                key=lambda r: r.sequence, reverse=True
            )
            for line in line_ids:
                line.refresh()
            record._update_summary()
            record._calc_budget_amount()

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
