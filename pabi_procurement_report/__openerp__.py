# -*- coding: utf-8 -*-
{
    'name': 'NSTDA :: Procurement Report',
    'version': '8.0.1.0.0',
    'category': 'Purchase',
    'description': """
""",
    'author': 'Ecosoft',
    'website': 'http://ecosoft.co.th',
    'depends': [
        'report_xls',
        'pabi_procurement',
        'pabi_purchase_work_acceptance',
        'pabi_asset_management',
        'pabi_purchase_contract',
        'pabi_utils',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizards/pabi_purchase_summarize_report_wizard.xml',
        # Created using pabi_utils xlsx_template
        'reports/xlsx_report_pabi_purchase_summarize.xml',
        'reports/xlsx_report_pabi_standard_asset.xml',
        'reports/xlsx_report_pabi_stock_card_for_accounting.xml',
        'reports/xlsx_report_pabi_monthly_work_acceptance.xml',
        'reports/xlsx_report_pabi_sla_balance.xml',
        'reports/xlsx_report_pabi_supplier_list.xml',
        'reports/xlsx_report_pabi_stock_balance.xml',
        'reports/xlsx_report_pabi_supplier_evaluation.xml',
        'reports/xlsx_report_pabi_comparison_pr_po.xml',
        'xlsx_template/templates.xml',
        'xlsx_template/load_template.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
