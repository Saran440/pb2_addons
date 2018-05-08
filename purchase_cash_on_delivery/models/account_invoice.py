# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    is_prepaid = fields.Boolean(
        string='Cash on Delivery',
        compute='_compute_is_prepaid',
        store=True,
    )
    clear_prepaid_move_id = fields.Many2one(
        'account.move',
        string='Clear Prepaid Journal Entry',
        readonly=True,
        index=True,
        ondelete='restrict',
        copy=False,
    )
    purchase_ids = fields.Many2many(
        'purchase.order',
        'purchase_invoice_rel', 'invoice_id', 'purchase_id',
        copy=False,
        string='Purchase Orders',
        readonly=True,
        help="This is the list of purchase orders linked to this invoice.",
    )

    @api.multi
    @api.depends('payment_term')
    def _compute_is_prepaid(self):
        cod_pay_term = self.env.ref('purchase_cash_on_delivery.'
                                    'cash_on_delivery_payment_term', False)
        for rec in self:
            rec.is_prepaid = rec.payment_term == cod_pay_term

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        cod_pay_term = self.env.ref('purchase_cash_on_delivery.'
                                    'cash_on_delivery_payment_term')
        # For prepaid only
        if self.payment_term == cod_pay_term:
            journal = self.env.ref('purchase_cash_on_delivery.'
                                   'clear_prepaid_journal')
            if not journal.default_debit_account_id or \
                    not journal.default_credit_account_id:
                raise ValidationError(
                    _('Clear Prepaid Journal has not been setup properly!\n'
                      'Make sure default accounts are Prepaid account'))
            account = journal.default_debit_account_id
            # Find lines to merge
            ml = filter(lambda x: x[2]['account_id'] == account.id,
                        move_lines)
            # Filter for non merged lines
            move_lines = filter(lambda x: x[2]['account_id'] != account.id,
                                move_lines)
            merged_ml = {
                'analytic_account_id': False,
                'tax_code_id': False,
                'analytic_lines': [],
                'tax_amount': 0.0,
                'name': False,  # To merge use account.name
                'ref': False,  # Should be same
                'currency_id': False,  # Should be same
                'credit': 0.0,  # To merge
                'product_id': False,
                'date_maturity': False,  # Should be same
                'debit': 0.0,  # To merge
                'date': False,  # Should be same
                'amount_currency': 0.0,  # To merge
                'product_uom_id': False,
                'quantity': 1.0,
                'partner_id': False,  # Should be same
                'account_id': False  # Should be same
            }
            for l in ml:
                l = l[2]  # get dict form
                merged_ml.update({
                    'name': account.name,
                    'ref': l['ref'],
                    'currency_id': l['currency_id'],
                    'credit': merged_ml['credit'] + l['credit'],
                    'date_maturity': l['date_maturity'],
                    'debit': merged_ml['debit'] + l['debit'],
                    'date': l['date'],
                    'amount_currency': (merged_ml['amount_currency'] +
                                        l['amount_currency']),
                    'partner_id': l['partner_id'],
                    'account_id': l['account_id'],
                })
            move_lines = [(0, 0, merged_ml)] + move_lines
        move_lines = super(AccountInvoice, self).\
            finalize_invoice_move_lines(move_lines)
        return move_lines

    @api.multi
    def clear_prepaid(self):
        for invoice in self:
            if not all(x for x in invoice.purchase_ids.mapped('shipped')):
                raise ValidationError(
                    _('Not all items in related order has been shipped!'))
            invoice.action_move_create()

    @api.model
    def line_get_convert(self, line, part, date):
        res = super(AccountInvoice, self).line_get_convert(line, part, date)
        if self._context.get('is_clear_prepaid', False) and \
                line['type'] == 'dest':
            journal = self.env.ref('purchase_cash_on_delivery.'
                                   'clear_prepaid_journal')
            res.update({'account_id': journal.default_credit_account_id.id})
        return res

    @api.multi
    def write(self, vals):
        if self._context.get('is_clear_prepaid', False):
            if 'move_id' in vals:
                vals['clear_prepaid_move_id'] = vals.pop('move_id')
        return super(AccountInvoice, self).write(vals)

    @api.model
    def _skip_check_move_id(self):
        if self._context.get('is_clear_prepaid', False):
            return True
        return super(AccountInvoice, self)._skip_check_move_id()

    @api.model
    def _get_journal_hook(self, ctx):
        """ HOOK """
        if self._context.get('is_clear_prepaid', False):
            journal = self.env.ref('purchase_cash_on_delivery.'
                                   'clear_prepaid_journal')
            return journal.with_context(ctx)
        return super(AccountInvoice, self)._get_journal_hook(ctx)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.model
    def move_line_get_item(self, line):
        res = super(AccountInvoiceLine, self).move_line_get_item(line)
        cod_pay_term = self.env.ref('purchase_cash_on_delivery.'
                                    'cash_on_delivery_payment_term')
        if line.invoice_id.payment_term == cod_pay_term and \
                not self._context.get('is_clear_prepaid', False):
            journal = self.env.ref('purchase_cash_on_delivery.'
                                   'clear_prepaid_journal')
            if not journal.default_debit_account_id or \
                    not journal.default_credit_account_id:
                raise ValidationError(
                    _('Clear Prepaid Journal has not been setup properly!\n'
                      'Make sure default accounts are Prepaid account'))
            res.update({'account_id': journal.default_debit_account_id.id})
        return res


class AccountInvoiceTax(models.Model):
    _inherit = 'account.invoice.tax'

    @api.model
    def move_line_get(self, invoice_id):
        # When clear prepaid, Tax are not considered
        if self._context.get('is_clear_prepaid', False):
            return []
        res = super(AccountInvoiceTax, self).move_line_get(invoice_id)
        return res
