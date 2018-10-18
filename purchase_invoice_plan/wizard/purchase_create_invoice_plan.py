# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError
from openerp.tools.float_utils import float_round as round
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_compare


class PurchaseCreateInvoicePlan(models.TransientModel):
    _name = 'purchase.create.invoice.plan'
    _description = 'Create Purchase Invoice Plan'

    @api.model
    def _default_order_amount(self):
        order = self.env['purchase.order'].\
            browse(self._context.get('active_id'))
        base_amount = order.amount_untaxed
        return base_amount

    use_advance = fields.Boolean(
        string='Advance on 1st Invoice',
        default=False,
    )
    use_deposit = fields.Boolean(
        string='1st Deposit Invoice',
        default=False,
    )
    num_installment = fields.Integer(
        string='Number of Installment',
        default=0,
    )
    installment_ids = fields.One2many(
        'purchase.create.invoice.plan.installment',
        'plan_id',
        string='Installments',
    )
    order_amount = fields.Float(
        string='Order Amount Untaxed',
        readonly=True,
        default=_default_order_amount,
    )
    invoice_mode = fields.Selection(
        [('change_price', 'As 1 Job (change price)'),
         ('change_quantity', 'As Units (change quantity)')
         ],
        string='Invoice Mode',
        required=True,
        default='change_quantity')
    installment_date = fields.Date(
        string='Installment Date',
        default=fields.Date.context_today,
        required=True,
    )
    interval = fields.Integer(
        string='Interval',
        default=1,
        required=True,
    )
    interval_type = fields.Selection(
        [('day', 'Day'),
         ('month', 'Month'),
         ('year', 'Year')],
        string='Interval Type',
        default='month',
        required=True,
    )
    installment_amount = fields.Float(
        string='Installment Amount',
        digits=dp.get_precision('Account'),
    )

    @api.onchange('use_advance')
    def _onchange_use_advance(self):
        if self.use_advance:
            self.use_deposit = False

    @api.onchange('use_deposit')
    def _onchange_use_deposit(self):
        if self.use_deposit:
            self.use_advance = False

    @api.model
    def _check_deposit_account(self):
        company = self.env.user.company_id
        account_id = company.account_deposit_supplier.id
        if not account_id:
            raise except_orm(
                _('Configuration Error!'),
                _('There is no deposit customer account '
                  'defined as global property.')
            )

    @api.model
    def _validate_total_amount(self):
        return True
        # obj_precision = self.env['decimal.precision']
        # prec = obj_precision.precision_get('Account')
        # amount_total = sum([x.installment > 0 and x.amount or
        #                     0.0 for x in self.installment_ids])
        # if round(amount_total, prec) != round(self.order_amount, prec):
        #     raise except_orm(
        #         _('Amount Mismatch!'),
        #         _("Total installment amount %d not "
        #           "equal to order amount %d!")
        #         % (amount_total, self.order_amount))

    @api.model
    def _check_installment_amount(self):
        if any([i.amount <= 0 for i in self.installment_ids]):
            raise ValidationError(
                _('Negative or zero installment amount not allowed!'))

    @api.multi
    def do_create_purchase_invoice_plan(self):
        self.ensure_one()
        self._validate_total_amount()
        self._check_installment_amount()
        self.env['purchase.invoice.plan']._validate_installment_date(
            self.installment_ids)
        order = self.env['purchase.order'].browse(self._context['active_id'])
        # order._check_invoice_mode()
        order.invoice_plan_ids.unlink()
        lines = []
        for install in self.installment_ids:
            if install.installment == 0:
                self._check_deposit_account()
                if install.is_advance_installment:
                    line_data = self._prepare_advance_line(order, install)
                    lines.append(line_data)
                if install.is_deposit_installment:
                    line_data = self._prepare_deposit_line(order, install)
                    lines.append(line_data)
            elif install.installment > 0:
                for order_line in order.order_line:
                    line_data = self._prepare_installment_line(order,
                                                               order_line,
                                                               install)
                    lines.append(line_data)
        order.invoice_plan_ids = lines
        order.write({'use_advance': self.use_advance,
                     'use_deposit': self.use_deposit,
                     'invoice_mode': self.invoice_mode,
                     'num_installment': self.num_installment,
                     })
        return True

    @api.model
    def _prepare_advance_line(self, order, install):
        return self._prepare_advance_deposit_line(order, install, True, False)

    @api.model
    def _prepare_deposit_line(self, order, install):
        return self._prepare_advance_deposit_line(order, install, False, True)

    @api.model
    def _prepare_advance_deposit_line(self, order, install, advance, deposit):
        obj_precision = self.env['decimal.precision']
        prec = obj_precision.precision_get('Account')
        base_amount = order.amount_untaxed
        data = {
            'order_id': order.id,
            'order_line_id': False,
            'installment': 0,
            'description': install.description,
            'is_advance_installment': advance,
            'is_deposit_installment': deposit,
            'date_invoice': install.date_invoice,
            'deposit_percent': install.percent,
            'deposit_amount': round(install.percent/100 *
                                    base_amount, prec)
        }
        return data

    @api.model
    def _prepare_installment_line(self, order, order_line, install):
        obj_precision = self.env['decimal.precision']
        prec = obj_precision.precision_get('Account')
        subtotal = order_line.price_subtotal
        data = {
            'order_id': order.id,
            'order_line_id': order_line.id,
            'description': order_line.name,
            'installment': install.installment,
            'date_invoice': install.date_invoice,
            'invoice_percent': install.percent,
            'invoice_amount': round(install.percent / 100 *
                                    subtotal, prec),
        }
        return data

    @api.model
    def _compute_installment_details(self):
        obj_precision = self.env['decimal.precision']
        prec = obj_precision.precision_get('Account')
        if self.installment_ids:
            installment_date =\
                datetime.strptime(self.installment_date, "%Y-%m-%d")
            count = 0
            remaining_installment_amount = self.order_amount
            last_line = False
            for i in self.installment_ids:
                if i.is_advance_installment or i.is_deposit_installment:
                    i.date_invoice = self.installment_date
                    continue
                interval = self.interval
                if count == 0:
                    interval = 0
                if self.interval_type == 'month':
                    installment_date =\
                        installment_date + relativedelta(months=+interval)
                elif self.interval_type == 'year':
                    installment_date =\
                        installment_date + relativedelta(years=+interval)
                else:
                    installment_date =\
                        installment_date + relativedelta(days=+interval)
                count += 1
                i.date_invoice = installment_date
                if float_compare(remaining_installment_amount,
                                 self.installment_amount, 2) == 1:
                    i.amount = self.installment_amount
                elif remaining_installment_amount < 0:
                    i.amount = 0
                else:
                    i.amount = remaining_installment_amount
                remaining_installment_amount = (remaining_installment_amount -
                                                self.installment_amount)
                new_val = i.amount / (self.order_amount or 1) * 100
                # if round(new_val, prec) != round(i.percent, prec):
                i.percent = new_val
                last_line = i
            if last_line and remaining_installment_amount > 0:
                last_line.amount = (last_line.amount +
                                    remaining_installment_amount)
                new_val = last_line.amount / self.order_amount * 100
                # if round(new_val, prec) != round(last_line.percent, prec):
                last_line.percent = new_val

    @api.onchange('use_advance', 'num_installment', 'use_deposit')
    def _onchange_plan(self):
        order = self.env['purchase.order'].\
            browse(self._context.get('active_id'))

        if self.num_installment > 0:
            self.installment_amount = self.order_amount / self.num_installment

        i = 1

        lines = []
        base_amount = order.amount_untaxed
        date_invoice = fields.Date.context_today(self)
        if self.use_advance:
            lines.append({'installment': 0,
                          'order_amount': base_amount,
                          'amount': 0,
                          'description': 'Advance Amount',
                          'is_advance_installment': True,
                          'percent': 0,
                          'date_invoice': date_invoice})

        if self.use_deposit:
            lines.append({'installment': 0,
                          'order_amount': base_amount,
                          'amount': 0,
                          'description': 'Deposit Amount',
                          'is_deposit_installment': True,
                          'percent': 0,
                          'date_invoice': date_invoice})

        while i <= self.num_installment:
            lines.append({'installment': i,
                          'order_amount': base_amount,
                          'amount': i == 1 and base_amount or 0,
                          'percent': i == 1 and 100 or 0,
                          'date_invoice': date_invoice})
            i += 1

        self.installment_ids = False
        self.installment_ids = lines

        self._compute_installment_details()

    @api.one
    @api.onchange('installment_date',
                  'interval_type',
                  'interval',
                  'installment_amount')
    def _onchange_installment_config(self):
        self._compute_installment_details()


class PurchaseCreateInvoicePlanInstallment(models.TransientModel):
    _name = 'purchase.create.invoice.plan.installment'
    _description = 'Create Purchase Invoice Plan Installments'

    plan_id = fields.Many2one(
        'purchase.create.invoice.plan',
        string='Wizard Reference',
        readonly=True,
    )
    installment = fields.Integer(
        string='Installment',
        readonly=True,
        help="Group of installment. "
        "Each group will be an invoice",
    )
    date_invoice = fields.Date(
        string='Invoice Date',
        required=True,
        help="Invoice created for this installment will be using this date",
    )
    order_amount = fields.Float(
        string='Order Amount',
    )
    percent = fields.Float(
        string='%',
        digits=(16, 10),
    )
    amount = fields.Float(
        string='Amount',
        digits=dp.get_precision('Account'),
    )
    is_deposit_installment = fields.Boolean(
        string='Deposit Installment',
    )
    is_advance_installment = fields.Boolean(
        string='Advance Installment',
    )
    description = fields.Char(
        string='Description',
        size=500,
    )

    @api.onchange('percent')
    def _onchange_percent(self):
        obj_precision = self.env['decimal.precision']
        prec = obj_precision.precision_get('Account')
        self.amount = round(self.order_amount * self.percent / 100, prec)

    @api.onchange('amount')
    def _onchange_amount(self):
        obj_precision = self.env['decimal.precision']
        prec = obj_precision.precision_get('Account')
        if not self.order_amount:
            raise Warning(_('Order amount equal to 0.0!'))
        new_val = self.amount / self.order_amount * 100
        if round(new_val, prec) != round(self.percent, prec):
            self.percent = new_val

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
