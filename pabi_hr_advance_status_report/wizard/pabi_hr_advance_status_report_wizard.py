# -*- coding: utf-8 -*-
from openerp import models, fields, api

import time

class PabiHrAdvanceStatusReportWizard(models.TransientModel):

    _name = 'pabi.hr.advance.status.report.wizard'

    run_date = fields.Date(string="Run Date", default=time.strftime("%Y-%m-%d"))

    report_type = fields.Selection(
        [('status', 'Status'),
         ('summary', 'Summary'),
         ('detail', 'Detail')],
        string='Report type',
        required=True,
        default='status',
    )

    @api.multi
    def run_report(self):
        data = {'parameters': {}}
        Report = self.env['hr.expense.expense']

        report_name = 'pabi_hr_advance_status_report'
        ids = Report.search([('state', '=', 'paid'),('amount_to_clearing', '>', 0.0)],
                            order='operating_unit_id, employee_id, invoice_id')._ids

        if self.report_type == 'summary':
            report_name = 'pabi_hr_advance_status_summary_report'
        elif self.report_type == 'detail':
            report_name = 'pabi_hr_advance_status_detail_report'

        data['parameters']['ids'] = ids
        res = {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': data,
        }
        return res
