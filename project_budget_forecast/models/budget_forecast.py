# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BudgetForecast(models.Model):
    _name = "budget.forecast"
    _description = _name

    name = fields.Char("Name", compute="_compute_name")
    description = fields.Char("Description", copy=True)
    sequence = fields.Integer()
    analytic_id = fields.Many2one(
        "account.analytic.account",
        "Analytic Account",
        required=True,
        ondelete="restrict",
        index=True,
        copy=True,
    )

    main_category = fields.Many2one(
        "budget.forecast.category",
        help="Technical field for budget_forecast_category fields creation",
        ondelete="restrict",
    )
    is_summary = fields.Boolean(copy=False, default=False)
    summary_id = fields.Many2one("budget.forecast", store=True)

    display_type = fields.Selection(
        [
            ("line_section", "Section"),
            ("line_subsection", "Sub-Section"),
            ("line_article", "Article"),
            ("line_note", "Note"),
        ],
        help="Technical field for UX purpose.",
        copy=True,
    )

    product_id = fields.Many2one("product.product", copy=True)
    product_uom_id = fields.Many2one("uom.uom", string="Unit of Measure", copy=True)

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        string="Currency",
        readonly=True,
        store=True,
        compute_sudo=True,
        copy=True,
    )

    plan_qty = fields.Float("Plan Quantity", copy=False)
    plan_price = fields.Monetary("Plan Price", default=0.00, copy=False)
    plan_amount_without_coeff = fields.Monetary(
        "Plan Amount", compute="_calc_plan_amount_without_coeff", store=True, copy=False
    )
    plan_amount_with_coeff = fields.Monetary(
        "Plan Amount with coeff",
        compute="_calc_plan_amount_with_coeff",
        store=True,
        copy=False,
    )

    analytic_line_ids = fields.Many2many(
        "account.analytic.line", compute="_calc_line_ids", copy=False
    )
    actual_qty = fields.Float(
        "Actual Quantity",
        compute="_calc_actual",
        store=True,
        compute_sudo=True,
        copy=False,
    )
    actual_price = fields.Monetary(
        "Actual Price",
        compute="_calc_actual",
        store=True,
        compute_sudo=True,
        copy=False,
    )
    actual_amount = fields.Monetary(
        "Actual Amount",
        compute="_calc_actual",
        store=True,
        compute_sudo=True,
        copy=False,
    )
    diff_amount = fields.Monetary(
        "Diff", compute="_calc_actual", store=True, compute_sudo=True, copy=False
    )
    parent_id = fields.Many2one(
        "budget.forecast", store=True, compute_sudo=True, compute="_calc_parent_id"
    )
    child_ids = fields.One2many("budget.forecast", "parent_id", copy=False)

    note = fields.Text(string="Note")

    @api.model_create_multi
    @api.returns("self", lambda value: value.id)
    def create(self, vals_list):
        records = super(BudgetForecast, self).create(vals_list)
        records._create_category_sections()
        records._update_parent_plan()
        return records

    def _create_category_sections(self):
        for record in self:
            if (not record.main_category) and (
                record.display_type in ["line_section", "line_subsection"]
            ):
                record.is_summary = True
                for category in self.env["budget.forecast.category"].search([]):
                    values = {
                        "main_category": category.id,
                        "summary_id": record.id,
                        "is_summary": False,
                    }
                    record.copy(values)

    @api.onchange("description", "product_id")
    def _sync_sections_date(self):
        if self.display_type in ["line_section", "line_subsection"]:
            # find similar section/sub_section lines
            lines = self.env["budget.forecast"].search(
                [
                    "|",
                    ("summary_id", "=", self.summary_id.id),
                    ("id", "=", self.summary_id.id),
                ]
            )
            for line in lines:
                line.product_id = self.product_id.id
                line.description = self.description

    def write(self, vals):
        res = super(BudgetForecast, self).write(vals)
        self._update_parent_plan()
        return res

    def unlink(self, child_unlink=False):
        parent_ids = self.mapped("parent_id")
        if not child_unlink:
            for record in self:
                if record.display_type in [
                    "line_section",
                    "line_subsection",
                ]:
                    # find similar section/sub_section lines
                    lines = record.env["budget.forecast"].search(
                        [
                            ("id", "=", record.id),
                            "|",
                            ("summary_id", "=", record.summary_id.id),
                            ("id", "=", record.summary_id.id),
                        ]
                    )
                    for line in lines:
                        line.unlink(True)
        res = super(BudgetForecast, self).unlink()
        parent_ids.exists()._calc_plan()
        return res

    @api.onchange("description")
    def _compute_name(self):
        for record in self:
            record.name = record.description

    def refresh(self):
        self._calc_parent_id()
        self._calc_line_ids()
        self._calc_plan()
        self._update_parent_plan()
        self._calc_actual()
        self._update_parent_actual()
        self._update_summary()

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id and not self.description:
            self.description = self.product_id.name
        self.product_uom_id = self.product_id.uom_id
        if self.display_type == "line_article":
            self.plan_price = self.product_id.standard_price
        else:
            self._calc_plan_price()

    @api.depends("plan_qty", "plan_price", "child_ids")
    def _calc_plan_amount_without_coeff(self):
        for record in self:
            if record.child_ids:
                record.plan_amount_without_coeff = sum(
                    record.mapped("child_ids.plan_amount_without_coeff")
                )
            else:
                record.plan_amount_without_coeff = record.plan_qty * record.plan_price

    @api.depends("plan_qty", "plan_price", "child_ids")
    def _calc_plan_amount_with_coeff(self):
        for record in self:
            record.plan_amount_with_coeff = record.plan_amount_without_coeff * (
                1 + record.analytic_id.global_coeff
            )

    @api.depends("child_ids")
    def _calc_plan_qty(self):
        for record in self:
            if record.child_ids:
                record.plan_qty = sum(record.mapped("child_ids.plan_qty"))

    @api.depends("child_ids")
    def _calc_plan_price(self):
        for record in self:
            if record.display_type in ["line_section", "line_subsection"]:
                if record.child_ids:
                    lst = record.mapped("child_ids.plan_price")
                    if lst and (sum(lst) > 0):
                        record.plan_price = lst and sum(lst)
                    else:
                        record.plan_price = record.product_id.standard_price
                else:
                    record.plan_price = record.product_id.standard_price
            elif record.display_type == "line_note":
                record.plan_price = 0.00

    @api.depends(
        "analytic_id.budget_forecast_ids", "sequence", "parent_id", "child_ids"
    )
    def _calc_parent_id(self):
        for record in self:
            if record.display_type == "line_section":
                # A Section is the top of the line hierarchy => no parent
                record.parent_id = False
                continue
            found = False
            parent_id = False
            for line in record.analytic_id.budget_forecast_ids.search(
                [
                    ("analytic_id", "=", record.analytic_id.id),
                    ("main_category", "=", record.main_category.id),
                ]
            ).sorted(key=lambda r: r.sequence, reverse=True):
                if not found and line != record:
                    continue
                if line == record:
                    found = True
                    continue
                if line.display_type in ["line_article", "line_note"]:
                    continue
                elif line.display_type == "line_subsection":
                    if record.display_type in ["line_article", "line_note"]:
                        parent_id = line
                        break
                    else:
                        continue
                elif line.display_type == "line_section":
                    parent_id = line
                    break
            record.parent_id = parent_id

    @api.depends("analytic_id", "child_ids")
    def _calc_line_ids(self):
        for record in self:
            domain = [
                ("account_id", "=", record.analytic_id.id),
                ("company_id", "=", record.company_id.id),
                ("product_id", "=", record.product_id.id),
            ]
            record.analytic_line_ids = self.env["account.analytic.line"].search(domain)

    @api.depends("analytic_id.line_ids.amount")
    def _calc_actual(self):
        for record in self:
            child_actual_qty = 0
            child_actual_amount = 0
            if record.child_ids:
                child_actual_qty = sum(record.mapped("child_ids.actual_qty"))
                child_actual_amount = sum(record.mapped("child_ids.actual_amount"))
            line_ids = record.analytic_line_ids
            record.actual_qty = (
                abs(sum(line_ids.mapped("unit_amount"))) + child_actual_qty
            )
            record.actual_amount = -sum(line_ids.mapped("amount")) + child_actual_amount
            record.actual_price = abs(
                record.actual_qty and record.actual_amount / record.actual_qty
            )
            record.diff_amount = record.plan_amount_with_coeff - record.actual_amount

    def _calc_plan(self):
        self._calc_plan_qty()
        self._calc_plan_price()
        self._calc_plan_amount_without_coeff()
        self._calc_plan_amount_with_coeff()

    def _update_parent_plan(self):
        self.exists().mapped("parent_id")._calc_plan()

    def _update_parent_actual(self):
        self.exists().mapped("parent_id")._calc_actual()

    def _update_summary(self):
        for record in self:
            if self.display_type in ["line_section", "line_subsection"]:
                # find the summary section/sub_section line
                summary_line = self.env["budget.forecast"].search(
                    [
                        ("id", "=", self.summary_id.id),
                    ],
                    limit=1,
                )
                # find similar section/sub_section lines
                similar_lines = self.env["budget.forecast"].search(
                    [
                        ("summary_id", "=", self.summary_id.id),
                        ("id", "!=", self.id),
                    ]
                )
                # Calculate the total amounts
                summary_line.plan_amount_without_coeff = 0
                summary_line.plan_amount_with_coeff = 0
                summary_line.actual_amount = 0
                for line in similar_lines:
                    summary_line.plan_amount_without_coeff += (
                        line.plan_amount_without_coeff
                    )
                    summary_line.plan_amount_with_coeff += line.plan_amount_with_coeff
                    summary_line.actual_amount += line.actual_amount
