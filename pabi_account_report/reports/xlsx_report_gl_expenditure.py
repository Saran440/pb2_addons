# -*- coding: utf-8 -*-
from openerp import models, fields, api


class PabiCommonAccountReportView(models.Model):
    _inherit = 'pabi.common.account.report.view'

    budget_fund_rule_line_id = fields.Many2one(
        'budget.fund.rule.line',
        string='Budget Fund Rule Line',
        compute='_compute_budget_fund_rule_line',
    )

    @api.multi
    def _compute_budget_fund_rule_line(self):
        for rec in self:
            Fund = self.env['budget.fund.rule.line']
            domain = ([('fund_rule_id.fund_id', '=', rec.fund_id.id),
                       ('fund_rule_id.project_id', '=', rec.project_id.id),
                       ('fund_rule_id.state', '=', 'confirmed'),
                       ('account_ids', 'in', rec.account_id.id)])
            lines = Fund.search(domain)
            if len(lines) > 1:
                rec.budget_fund_rule_line_id = lines[0]
            rec.budget_fund_rule_line_id = lines


class XLSXReportGlExpenditure(models.TransientModel):
    _name = 'xlsx.report.gl.expenditure'
    _inherit = 'report.account.common'

    account_ids = fields.Many2many(
        'account.account',
        string='Account Code',
    )
    chart_view = fields.Selection(
        [('personnel', 'Personnel'),
         ('invest_asset', 'Investment Asset'),
         ('unit_base', 'Unit Based'),
         ('project_base', 'Project Based'),
         ('invest_construction_phase', 'Investment Construction Phase')],
        string='Budget View',
        required=True,
    )
    org_ids = fields.Many2many(
        'res.org',
        string='Org',
    )
    invest_asset_ids = fields.Many2many(
        'res.invest.asset',
        string='Investment Asset',
    )
    section_ids = fields.Many2many(
        'res.section',
        string='Section',
    )
    fund_ids = fields.Many2many(
        'res.fund',
        string='Source of Fund',
    )
    project_ids = fields.Many2many(
        'res.project',
        string='Project',
    )
    invest_construction_phase_ids = fields.Many2many(
        'res.invest.construction.phase',
        string='Project (C)',
    )
    activity_group_ids = fields.Many2many(
        'account.activity.group',
        string='Activity Group',
    )
    activity_ids = fields.Many2many(
        'account.activity',
        string='Activity',
    )
    results = fields.Many2many(
        'pabi.common.account.report.view',
        string='Results',
        compute='_compute_results',
        help='Use compute fields, so there is nothing store in database',
    )

    @api.onchange('chart_view')
    def _onchange_chart_view(self):
        self.org_ids = False
        self.invest_asset_ids = False
        self.section_ids = False
        self.fund_ids = False
        self.project_ids = False
        self.invest_construction_phase_ids = False

    @api.multi
    def _compute_results(self):
        self.ensure_one()
        Result = self.env['pabi.common.account.report.view']
        dom = []
        if self.account_ids:
            dom += [('account_id', 'in', self.account_ids.ids)]
        if self.activity_group_ids:
            dom += [('activity_group_id', 'in', self.activity_group_ids.ids)]
        if self.activity_ids:
            dom += [('activity_id', 'in', self.activity_ids.ids)]
        # Filter chart view
        if self.chart_view == 'personnel':
            dom += [('invoice_move_line_id.org_id', '!=', False)]
        elif self.chart_view == 'invest_asset':
            dom += [('invoice_move_line_id.invest_asset_id', '!=', False)]
        elif self.chart_view == 'unit_base':
            dom += [('invoice_move_line_id.section_id', '!=', False)]
        elif self.chart_view == 'project_base':
            dom += [('invoice_move_line_id.project_id', '!=', False)]
        else:
            dom += [('invoice_move_line_id.invest_construction_phase_id', '!=',
                     False)]
        if self.org_ids:
            dom += [('invoice_move_line_id.org_id', 'in', self.org_ids.ids)]
        if self.invest_asset_ids:
            dom += [('invoice_move_line_id.invest_asset_id', 'in',
                     self.invest_asset_ids.ids)]
        if self.section_ids:
            dom += [('invoice_move_line_id.section_id', 'in',
                     self.section_ids.ids)]
        if self.fund_ids:
            dom += [('invoice_move_line_id.fund_id', 'in', self.fund_ids.ids)]
        if self.project_ids:
            dom += [('invoice_move_line_id.project_id', 'in',
                     self.project_ids.ids)]
        if self.invest_construction_phase_ids:
            dom += [('invoice_move_line_id.invest_construction_phase_id', 'in',
                     self.invest_construction_phase_ids.ids)]
        # Filter date
        if self.fiscalyear_start_id:
            dom += [('invoice_move_line_id.date', '>=',
                     self.fiscalyear_start_id.date_start)]
        if self.fiscalyear_end_id:
            dom += [('invoice_move_line_id.date', '<=',
                     self.fiscalyear_end_id.date_stop)]
        if self.period_start_id:
            dom += [('invoice_move_line_id.date', '>=',
                     self.period_start_id.date_start)]
        if self.period_end_id:
            dom += [('invoice_move_line_id.date', '<=',
                     self.period_end_id.date_stop)]
        if self.date_start:
            dom += [('invoice_move_line_id.date', '>=', self.date_start)]
        if self.date_end:
            dom += [('invoice_move_line_id.date', '<=', self.date_end)]
        self.results = Result.search(dom)
