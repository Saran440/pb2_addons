# -*- coding: utf-8 -*-
from openerp import models, api


class AccountBudget(models.Model):
    _inherit = 'account.budget'

    BUDGET_LEVEL = {
        # Code not cover Activity level yet
        # 'activity_group_id': 'Activity Group',
        # 'activity_id': 'Activity',
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
        'personnel_costcenter_id': 'Personnel Costcenter',
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
        #'invest_asset_categ_id': 'res.invest.asset.category',
        'invest_asset_id': 'res.invest.asset',
        # - Construction
        'invest_construction_id': 'res.invest.construction',
        'invest_construction_phase_id': 'res.invest.construction.phase',
    }

    BUDGET_LEVEL_TYPE = {
        'check_budget_project_base': 'Project Based',
        'check_budget_unit_base': 'Unit Based',
        'check_budget_personnel': 'Personnel',
        'check_budget_invest_asset': 'Investment Asset',
        'check_budget_invest_construction': 'Investment Construction',
    }

    @api.multi
    def _validate_budget_level(self, budget_type='check_budget'):
        for rec in self:
            budget_type = 'check_budget_%s' % (rec.chart_view,)
            super(AccountBudget, rec)._validate_budget_level(budget_type)

    @api.model
    def _get_budget_type_by_selected_chartfield(self, vals):
        if vals.get('project_id'):
            return 'check_budget_project_base'
        if vals.get('section_id'):
            return 'check_budget_unit_base'
        if vals.get('invest_asset_id'):
            return 'check_budget_invest_asset'
        if vals.get('invest_construction_phase_id'):
            return 'check_budget_invest_construction'
        if vals.get('personnel_costcenter_id'):
            return 'check_budget_personnel'
        return False

    # -- Budget Check for Activity Group Level --
    # DO NOT DELETE
#     @api.model
#     def _get_budget_monitor(self, fiscal, budget_type,
#                             budget_level, resource, pu_id=False):
#         """ Overwrite """
#         if budget_type not in ['check_budget_unit_base',
#                                'check_budget_project_base']:
#             return super(AccountBudget, self)._get_budget_monitor(fiscal,
#                                                                   budget_level,
#                                                                   resource,
#                                                                   pu_id)
#         monitors = False
#         if budget_level in ('activity_group_id', 'activity_id'):
#             if budget_type == 'check_budget_unit_base':
#                 monitors = resource.monitor_unit_ids.\
#                     filtered(lambda x: x.fiscalyear_id == fiscal).\
#                     filtered(lambda x: x['costcenter_id'].id == pu_id)
#             elif budget_type == 'check_budget_project_base':
#                 monitors = resource.monitor_ids.\
#                     filtered(lambda x: x.fiscalyear_id == fiscal).\
#                     filtered(lambda x: x['project_id'].id == pu_id)
#         else:
#             monitors = resource.monitor_ids.\
#                 filtered(lambda x: x.fiscalyear_id == fiscal)
#         return monitors
