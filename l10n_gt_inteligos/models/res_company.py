# -*- coding: utf-8 -*-

from odoo import fields, models, api, Command


class ResCompanyInherit(models.Model):
    _inherit = "res.company"

    # ----------------------------------------------------------
    # l10n_gt_td_generic
    # ----------------------------------------------------------
    duplicate_nit = fields.Boolean(
        store=True,
        index=True,
        string="¿Existiran NITs duplicados?",
    )
    payment_day = fields.Integer(
        default=4,
        store=True,
        index=True,
        string="Día de pago"
    )
    l10n_latam_document_type_id = fields.Many2one(
        comodel_name='l10n_latam.document.type', string='Tipo Documento predeterminado', copy=False
    )

    # ----------------------------------------------------------
    # gt_territorial_division
    # ----------------------------------------------------------
    county_id = fields.Many2one(
        'gt.county',
        store=True,
        copy=False,
        domain="[('state_id', '=', state_id)]",
        string="Municipio",
        index=True,
        help='Ingrese el municipio para la compañía.'
    )

    def _localization_use_documents(self):
        """Extensión del método para la localización a Guatemala de los documentos."""
        self.ensure_one()
        return self.account_fiscal_country_id.code == "GT" or super()._localization_use_documents()

    @api.model_create_multi
    def create(self, vals_list):
        """Extensión para vincular la compañía con el partner creado."""
        company = super(ResCompanyInherit, self).create(vals_list)
        for vals in vals_list:
            if vals.get('partner_id'):
                partner = self.env['res.partner'].sudo().browse(vals['partner_id'])
                if partner:
                    partner.sudo().write({'company_id': company.id})
        return company
