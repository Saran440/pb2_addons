# -*- coding: utf-8 -*-
from openerp import models, api, _
from openerp.exceptions import ValidationError, Warning as UserError


class AccountBudget(models.Model):
    _inherit = 'account.budget'

    BUDGET_LEVEL = {
        # Code not cover Activity level yet
        # 'activity_group_id': 'Activity Group',
        # 'activity_id': 'Activity',
        # Fund
        'fund_id': 'Fund (for all)',
        # Project Based
        'spa_id': 'SPA',
        'mission_id': 'Mission',
        'functional_area_id': 'Functional Area',
        'program_group_id': 'Program Group',
        'program_id': 'Program',
        'project_group_id': 'Project Group',
        'project_id': 'Project',
        # Unit Based
        'org_id': 'Org',
        'sector_id': 'Sector',
        'subsector_id': 'Subsector',
        'division_id': 'Division',
        'section_id': 'Section',
        'costcenter_id': 'Costcenter',
        # Personnel
        'personnel_costcenter_id': 'Personnel Budget',
        # Investment
        # - Asset
        # 'invest_asset_categ_id': 'Invest. Asset Category',  # (not dimension)
        'invest_asset_id': 'Invest. Asset',
        # - Construction
        'invest_construct_id': 'Construction',
        'invest_construction_phase_id': 'Construction Phase',
    }

    BUDGET_LEVEL_MODEL = {
        # Code not cover Activity level yet
        # 'activity_group_id': 'account.activity.group',
        # 'activity_id': 'Activity'  # No Activity Level{
        'fund_id': 'res.fund',

        'spa_id': 'res.spa',
        'mission_id': 'res.mission',
        'tag_type_id': 'res.tag.type',
        'tag_id': 'res.tag',
        # Project Based
        'functional_area_id': 'res.functional.area',
        'program_group_id': 'res.program.group',
        'program_id': 'res.program',
        'project_group_id': 'res.project.group',
        'project_id': 'res.project',
        # Unit Based
        'org_id': 'res.org',
        'sector_id': 'res.sector',
        'subsector_id': 'res.subsector',
        'division_id': 'res.division',
        'section_id': 'res.section',
        'costcenter_id': 'res.costcenter',
        # Personnel
        'personnel_costcenter_id': 'res.personnel.costceter',
        # Investment
        # - Asset
        # 'invest_asset_categ_id': 'res.invest.asset.category',
        'invest_asset_id': 'res.invest.asset',
        # - Construction
        'invest_construction_id': 'res.invest.construction',
        'invest_construction_phase_id': 'res.invest.construction.phase',
    }

    BUDGET_LEVEL_TYPE = {
        'project_base': 'Project Based',
        'unit_base': 'Unit Based',
        'personnel': 'Personnel',
        'invest_asset': 'Investment Asset',
        'invest_construction': 'Investment Construction',
    }

    @api.multi
    def _validate_budget_level(self, budget_type='check_budget'):
        for rec in self:
            budget_type = rec.chart_view
            super(AccountBudget, rec)._validate_budget_level(budget_type)

    @api.model
    def _get_budget_monitor(self, fiscal, budget_type,
                            budget_level, resource,
                            ext_field=False,
                            ext_res_id=False):
        # For funding level, we go deeper
        if budget_level == 'fund_id':
            budget_type_dict = {
                'unit_base': 'monitor_section_ids',
                'project_base': 'monitor_project_ids',
                'personnel': 'monitor_personnel_costcenter_ids',
                'invest_asset': 'monitor_invest_asset_ids',
                'invest_construction':
                'monitor_invest_construction_phase_ids'}
            return resource[budget_type_dict[budget_type]].\
                filtered(lambda x:
                         (x.fiscalyear_id == fiscal and
                          x[ext_field].id == ext_res_id))
            raise ValidationError(
                _('Budget Check at Fund level require a compliment dimension'))
        else:
            return super(AccountBudget, self).\
                _get_budget_monitor(fiscal, budget_type,
                                    budget_level, resource)

    @api.model
    def get_document_query(self, head_table, line_table):
        query = """
            select %(sel_fields)s,
                coalesce(sum(l.price_subtotal), 0.0) amount
            from """ + line_table + """ l
            join """ + head_table + """ h on h.id = l.invoice_id
            where h.id = %(active_id)s
            group by %(sel_fields)s
        """
        return query

    @api.model
    def document_check_budget(self, query, budget_level_info,
                              fiscal_id, active_id):
        Budget = self.env['account.budget']
        # Check for all budget types
        for budget_type in dict(Budget.BUDGET_LEVEL_TYPE).keys():
            if budget_type not in budget_level_info:
                raise UserError(_('Budget level is not set!'))
            budget_level = budget_level_info[budget_type]
            sel_fields = [budget_level]
            if budget_level == 'fund_id':
                budget_type_dict = {
                    'unit_base': 'section_id',
                    'project_base': 'project_id',
                    'personnel': 'personnel_costcenter_id',
                    'invest_asset': 'investment_asset_id',
                    'invest_construction': 'invest_construction_phase_id'}
                sel_fields.append(budget_type_dict[budget_type])
            self._cr.execute(
                query % {'sel_fields': ','.join(['l.'+i
                                                 for i in sel_fields]),
                         'active_id': active_id}
            )
            # Check budget at this budgeting level
            for rec in self._cr.dictfetchall():
                if rec[budget_level]:  # If no value, do not check.
                    ext_field = (len(sel_fields) > 1 and
                                 sel_fields[1] or
                                 False)
                    ext_res_id = (len(sel_fields) > 1 and
                                  rec[sel_fields[1]] or
                                  False)
                    res = Budget.check_budget(fiscal_id,
                                              budget_type,
                                              budget_level,
                                              rec[budget_level],
                                              rec['amount'],
                                              ext_field=ext_field,
                                              ext_res_id=ext_res_id)
                    if not res['budget_ok']:
                        raise UserError(res['message'])
