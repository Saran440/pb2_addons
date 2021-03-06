# -*- coding: utf-8 -*-
from openerp import models, fields, api


class ResDoctype(models.Model):
    _name = 'res.doctype'
    _description = 'Doctype'

    name = fields.Char(
        string='Name',
        readonly=True,
        size=500,
    )
    refer_type = fields.Selection(
        [],
        string='Reference Document',
        readonly=True,
    )
    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Sequence',
        domain=[('special_type', '=', 'doctype')],
    )
    prefix = fields.Char(
        related='sequence_id.prefix',
        string='Prefix',
    )
    implementation = fields.Selection(
        [('standard', 'Standard'),
         ('no_gap', 'No gap'), ],
        related='sequence_id.implementation',
        string='Implementation',
    )
    fiscal_sequence_ids = fields.One2many(
        related='sequence_id.fiscal_ids',
        string='Sequences by fiscalyear',
    )

    @api.model
    def get_doctype(self, refer_type):
        doctype = self.search([('refer_type', '=', refer_type)], limit=1)
        return doctype
