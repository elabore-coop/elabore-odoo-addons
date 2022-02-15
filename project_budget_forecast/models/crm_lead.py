# -*- coding: utf-8 -*-

from odoo import _, models, fields, api
from odoo.exceptions import UserError


class Lead(models.Model):
    _inherit = "crm.lead"

    analytic_account = fields.Many2one(
        "account.analytic.account", "Analytic Account", required=False, index=True
    )
    plan_amount_with_coeff = fields.Float(
        related="analytic_account.plan_amount_with_coeff"
    )

    def action_budget_forecast(self):
        if not self.analytic_account:
            raise UserError(
                _(
                    "You must add an analytic account to build/access the budget forecast screen."
                )
            )
        return self.analytic_account.action_budget_forecast()

    def action_new_quotation(self):
        action = super(Lead, self).action_new_quotation()
        if self.analytic_account:
            action["context"]["default_analytic_account_id"] = self.analytic_account.id
        return action
