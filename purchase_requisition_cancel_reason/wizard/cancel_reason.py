# -*- coding: utf-8 -*-

from openerp import models, fields, api


class PurchaseRequisitionCancel(models.TransientModel):

    _name = 'purchase.requisition.cancel'

    cancel_reason_txt = fields.Char(
        string="Reason",
        readonly=False)

    @api.one
    def confirm_cancel(self):
        act_close = {'type': 'ir.actions.act_window_close'}
        requisition_ids = self._context.get('active_ids')
        if requisition_ids is None:
            return act_close
        assert len(requisition_ids) == 1, "Only 1 Call for Bids expected"
        requisition = self.env['purchase.requisition'].browse(requisition_ids)
        requisition.cancel_reason_txt = self.cancel_reason_txt
        requisition.signal_workflow('cancel_requisition')
        requisition.state = 'cancel'
        return act_close
