# -*- coding: utf-8 -*-
from lxml import etree
from openerp import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    line_item_summary = fields.Text(
        string='Items Summary',
        compute='_compute_line_item_summary',
        store=True,
        help="This field provide summary of items in move line with Qty."
    )
    date = fields.Date(
        string='Posting Date',  # Rename
    )
    date_document = fields.Date(
        string='Document Date',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
        default=lambda self: fields.Date.context_today(self),
    )

    @api.multi
    def _write(self, vals):
        # KV/DV
        if 'line_item_summary' in vals and vals.get('line_item_summary'):
            summary = vals.get('line_item_summary')
            self._write({'narration': summary})
        return super(AccountMove, self)._write(vals)

    @api.multi
    @api.depends('line_id.name')
    def _compute_line_item_summary(self):
        for rec in self:
            lines = rec.line_id.filtered(
                lambda l: l.name != '/'
                # and account_id.user_type.report_type in ('income', 'expense')
            )
            items = [x.name for x in lines]
            items = list(set(items))
            if items:
                rec.line_item_summary = ", ".join(items)


class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        # Option to filter only company's bank's account
        if self._context.get('company_bank_account_only', False):
            BankAcct = self.env['res.partner.bank']
            banks = BankAcct.search([
                ('state', '=', 'SA'),  # Only Saving Bank Account
                ('partner_id', '=', self.env.user.company_id.partner_id.id)])
            account_ids = banks.mapped('journal_id').\
                mapped('default_debit_account_id').ids
            args += [('id', 'in', account_ids)]
        return super(AccountAccount, self).name_search(name=name,
                                                       args=args,
                                                       operator=operator,
                                                       limit=limit)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    receipt = fields.Boolean(
        string='Use for Receipt',
        default=True,
        help="If checked, this journal will show only on customer payment",
    )
    payment = fields.Boolean(
        string='Use for Payment',
        default=True,
        help="If checked, this journal will show only on supplier payment",
    )

    @api.model
    def fields_view_get(self, view_id=None, view_type=False,
                        toolbar=False, submenu=False):
        res = super(AccountJournal, self).\
            fields_view_get(view_id=view_id, view_type=view_type,
                            toolbar=toolbar, submenu=submenu)
        if self._context.get('default_type', False) != 'bank':
            if view_type in ('tree', 'form'):
                tag = view_type == 'tree' and "/tree" or "/form"
                doc = etree.XML(res['arch'])
                nodes = doc.xpath(tag)
                for node in nodes:
                    node.set('create', 'false')
                    node.set('delete', 'false')
                res['arch'] = etree.tostring(doc)
        return res


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    revenue = fields.Boolean(
        string='Use for Revenue',
        default=True,
        help="If checked, this term will only show on SO and Cust INV",
    )
    expense = fields.Boolean(
        string='Use for Expense',
        default=True,
        help="If checked, this term will only show on PO and Sup INV",
    )

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        if 'invoice_type' in self._context:
            itype = self._context.get('invoice_type')
            if itype in ('out_invoice', 'out_refund', 'out_invoice_debitnote'):
                args += [('revenue', '=', True)]
            if itype in ('in_invoice', 'in_refund', 'in_invoice_debitnote'):
                args += [('expense', '=', True)]
        return super(AccountPaymentTerm, self).name_search(name=name,
                                                           args=args,
                                                           operator=operator,
                                                           limit=limit)
