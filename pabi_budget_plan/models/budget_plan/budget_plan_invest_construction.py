# -*- coding: utf-8 -*-
from openerp import tools
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from .budget_plan_common import BPCommon, BPLCommon, PrevFYCommon
from openerp.addons.account_budget_activity.models.account_activity \
    import ActivityCommon
# from openerp.addons.document_status_history.models.document_history import \
#     LogCommon


class BudgetPlanInvestConstruction(BPCommon, models.Model):
    _name = 'budget.plan.invest.construction'
    _inherit = ['mail.thread']
    _description = "Investment Construction Budget - Budget Plan"
    _order = 'fiscalyear_id desc, id desc'

    # COMMON
    plan_line_ids = fields.One2many(
        'budget.plan.invest.construction.line',
        'plan_id',
        string='Budget Plan Lines',
        copy=True,
        track_visibility='onchange',
    )
    plan_revenue_line_ids = fields.One2many(
        'budget.plan.invest.construction.line',
        'plan_id',
        string='Revenue Plan Lines',
        copy=True,
        domain=[('budget_method', '=', 'revenue')],  # Have domain
        track_visibility='onchange',
    )
    plan_expense_line_ids = fields.One2many(
        'budget.plan.invest.construction.line',
        'plan_id',
        string='Expense Plan Lines',
        copy=True,
        domain=[('budget_method', '=', 'expense')],  # Have domain
        track_visibility='onchange',
    )
    # Select Dimension - ORG
    org_id = fields.Many2one(
        'res.org',
        string='Org',
        required=True,
    )
    _sql_constraints = [
        ('uniq_plan', 'unique(org_id, fiscalyear_id)',
         'Duplicated budget plan for the same org is not allowed!'),
    ]

    @api.model
    def create(self, vals):
        name = self._get_doc_number(vals['fiscalyear_id'],
                                    'res.org', vals['org_id'])
        vals.update({'name': name})
        return super(BudgetPlanInvestConstruction, self).create(vals)

    @api.model
    def generate_plans(self, fiscalyear_id=None):
        if not fiscalyear_id:
            raise ValidationError(_('No fiscal year provided!'))
        # Find existing plans, and exclude them
        plans = self.search([('fiscalyear_id', '=', fiscalyear_id)])
        _ids = plans.mapped('org_id')._ids
        # Find sections
        orgs = self.env['res.org'].search([('id', 'not in', _ids),
                                           ('special', '=', False)])
        plan_ids = []
        for org in orgs:
            plan = self.create({'fiscalyear_id': fiscalyear_id,
                                'org_id': org.id,
                                'user_id': False})
            plan_ids.append(plan.id)

        # Special for Invest Construction, also create budget control too
        self.env['account.budget'].\
            generate_invest_construction_controls(fiscalyear_id)

        return plan_ids


class BudgetPlanInvestConstructionLine(BPLCommon, ActivityCommon,
                                       models.Model):
    _name = 'budget.plan.invest.construction.line'
    _description = "Investment Construction Budget - Budget Plan Line"

    # COMMON
    chart_view = fields.Selection(
        default='invest_construction',  # Investment Construction
    )
    plan_id = fields.Many2one(
        'budget.plan.invest.construction',
        string='Budget Plan',
        ondelete='cascade',
        index=True,
        required=True,
    )
    # Extra
    org_id = fields.Many2one(
        related='plan_id.org_id',
        store=True,
        readonly=True,
    )
    invest_construction_id = fields.Many2one(
        related='invest_construction_phase_id.invest_construction_id',
        store=True,
        readonly=True,
    )
    c_or_n = fields.Selection(
        [('continue', 'Continue'),
         ('new', 'New')],
        string='C/N',
        default='new',
    )
    # From Project Construction Master Data
    month_duration = fields.Integer(
        string='Months',
    )
    date_start = fields.Date(
        string='Project Start Date',
    )
    date_end = fields.Date(
        string='Project End Date',
    )
    pm_employee_id = fields.Many2one(
        'hr.employee',
        string='Project Manager',
    )
    pm_section_id = fields.Many2one(
        'res.section',
        string='Owner Section',
    )
    operation_area = fields.Char(
        string='Operation Area',
    )
    date_expansion = fields.Date(
        string='Expansion Date',
    )
    project_readiness = fields.Text(
        string='Project Readiness',
    )
    reason = fields.Text(
        string='Reason',
    )
    expected_result = fields.Text(
        string='Expected Result',
    )
    budget_overall = fields.Float(
        string='Overall Budget',
    )
    amount_fy1 = fields.Float(
        string='FY1',
    )
    amount_fy2 = fields.Float(
        string='FY2',
    )
    amount_fy3 = fields.Float(
        string='FY3',
    )
    amount_fy4 = fields.Float(
        string='FY4',
    )
    amount_fy5 = fields.Float(
        string='FY5',
    )
    amount_beyond = fields.Float(
        string='Beyond FY5',
    )
    planned = fields.Float(
        string='Current Plan',
    )
    released = fields.Float(
        string='Current Released',
    )
    all_commit = fields.Float(
        string='Current All Commit',
    )
    po_commit = fields.Float(
        string='Current PO Commit',
    )
    pr_commit = fields.Float(
        string='Current PR Commit',
    )
    actual = fields.Float(
        string='Current Actual',
    )
    consumed = fields.Float(
        string='Current Consumed',
    )
    balance = fields.Float(
        string='Current Balance',
    )

    # Required for updating dimension
    # FIND ONLY WHAT IS NEED AND USE related field.

    @api.multi
    def edit_invest_construction(self):
        self.ensure_one()
        action = self.env.ref(
            'pabi_budget_plan.'
            'act_budget_plan_invest_construction_line_view')
        result = action.read()[0]
        view = self.env.ref('pabi_budget_plan.'
                            'view_budget_plan_invest_construction_line_form')
        result.update(
            {'res_id': self.id,
             'view_id': False,
             'view_mode': 'form',
             'views': [(view.id, 'form')],
             'context': False, })
        return result


class BudgetPlanInvestConstructionPrevFYView(PrevFYCommon, models.Model):
    """ Prev FY Performance view, must named as [model]+perv.fy.view """
    _name = 'budget.plan.invest.construction.prev.fy.view'
    _auto = False
    _description = 'Prev FY budget performance for construction'
    # Extra variable for this view
    _chart_view = 'invest_construction'
    _ex_view_fields = ['invest_construction_phase_id', 'org_id']
    _ex_domain_fields = ['org_id']  # Each plan is by this domain
    _ex_active_domain = \
        [('invest_construction_phase_id.state', '=', 'approve')]

    org_id = fields.Many2one(
        'res.org',
        string='Org',
        readonly=True,
    )
    invest_construction_phase_id = fields.Many2one(
        'res.invest.construction.phase',
        string='Construction Phase',
        readonly=True,
    )

    @api.multi
    def _prepare_prev_fy_lines(self):
        """ Given search result from this view, prepare lines tuple """
        plan_lines = []
        for rec in self:
            val = {'c_or_n': 'continue',
                   'invest_construction_phase_id':
                   rec.invest_construction_phase_id.id,
                   # ???
                   }
            plan_lines.append((0, 0, val))
        return plan_lines
