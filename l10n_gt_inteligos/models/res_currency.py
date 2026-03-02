# -*- coding: utf-8 -*-

from odoo.fields import Char
from odoo.models import Model
from odoo.api import (depends, depends_context)
from odoo import fields


class ResCurrency(Model):
    """Herencia de objeto para agregar campos para los montos en letras"""
    _inherit = 'res.currency'

    amount_separator = Char(string="Unidad/Subunidad Separador de Texto")
    close_financial_text = Char(string="Cierre Financiero, texto")

    country_code = fields.Char(string="Country code", compute="_compute_current_company_country_code")

    def _compute_current_company_country_code(self):
        for record in self:
            record.country_code = self.env.company.account_fiscal_country_id.code
