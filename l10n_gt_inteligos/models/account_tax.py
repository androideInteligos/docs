
from odoo import models, fields, api


class InheritAccountMove(models.Model):
    _inherit = 'account.tax'

    # -------------------------
    # gt_territorial_division #
    # -------------------------
    gt_state_id = fields.Many2one(
        'res.country.state',
        ondelete="set null",
        store=True,
        copy=False,
        string="Departamento",
        index=True,
        help='Ingrese el departamento al que pertenece el impuesto'
    )
    gt_county_id = fields.Many2one(
        'gt.county',
        ondelete="set null",
        store=True,
        copy=False,
        string="Municipio",
        index=True,
        help='Ingrese el municipo al que pertenece el impuesto'
    )

    # ---------------------------------
    # For Sale Purchase Ledger Report #
    # ---------------------------------

    group_type = fields.Selection(
        selection=[
            ('vat', 'IVA'),
            ('nvat', 'Otros Impuestos de Venta'),
            ('idp', 'IDP'),
            ('dai', 'DAI'),
            ('other', 'Otros Impuestos')
        ],
        string="Tipo de Impuesto"
    )

    @api.onchange('country_id')
    def _onchange_country(self):
        if self.country_code == 'GT':
            for rec in self:
                return {'domain': {'gt_state_id': [('country_id', '=', rec.country_id.id)]}}

    @api.onchange('gt_state_id')
    def _onchange_state_id(self):
        if self.country_code == 'GT':
            for rec in self:
                return {'domain': {'gt_county_id': [('state_id', '=', rec.gt_state_id.id)]}}
