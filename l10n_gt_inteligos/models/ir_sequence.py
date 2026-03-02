# -*- coding: utf-8 -*-

from odoo import models, fields


class IrSequenceInherited(models.Model):
    _inherit = 'ir.sequence'

    journal_id = fields.Many2one(comodel_name='account.journal', string='Diario')
    l10n_latam_document_type_id = fields.Many2one(comodel_name='l10n_latam.document.type', string='Tipo de documento')

    country_code = fields.Char(string="Country code", compute="_compute_current_company_country_code")

    def _compute_current_company_country_code(self):
        for record in self:
            record.country_code = self.env.company.account_fiscal_country_id.code
