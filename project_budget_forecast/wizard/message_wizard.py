# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BudgetForecastMessageWizard(models.TransientModel):
    _name = "budget.forecast.message.wizard"
    _description = "Show Message"

    message = fields.Text("Message", required=True)

    def action_close(self):
        return {"type": "ir.actions.act_window_close"}
