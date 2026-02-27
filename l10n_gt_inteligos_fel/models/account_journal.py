# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrderInherited(models.Model):
    _inherit = "account.journal"

    establishment_name = fields.Char(
        help="Campo de valor caracter, que identifica el nombre del establecimiento. Siendo útil para Facturación FEL",
        string="Nombre del Establecimiento"
    )

    establishment_number = fields.Integer(
        help="Campo de valor entero, que identifica el # establecimiento. Siendo útil para Facturación FEL",
        string="No. de Establecimiento"
    )
    country_id = fields.Many2one(
        comodel_name='res.country',
        default=lambda self: self.company_id.country_id,
        domain="[('code', 'in', ('GT', 'MX', 'SV', 'HN'))]",
        string="País",
        help='Ingrese el país en el que se encuentra el punto de venta.'
    )
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        domain="[('country_id.code', 'in', ('GT', 'MX', 'SV', 'HN'))]",
        string="Departamento",
        help='Ingrese el departamento en el que se encuentra el punto de venta.'
    )
    county_id = fields.Many2one(
        comodel_name='gt.county',
        domain="[('state_id', '=', state_id)]",
        string="Municipio",
        help='Ingrese el municipio en el que se encuentra el punto de venta.'
    )
    street = fields.Char(
        help="Campo que identifica dirección de establecimiento. Siendo útil para Facturación FEL",
        string="Dirección"
    )
    zip_code = fields.Char(
        help="Campo que identifica el código postal según dirección de establecimiento. "
             "Siendo útil para Facturación FEL",
        string="Código Postal"
    )

    its_fel = fields.Boolean(string="Genera Factura Electrónica", default=False)

    fel_phrases_ids = fields.Many2many('account.fel_phrases', 'account_journal_fel_phrase_rel',
                                       'journal_id', 'fel_phrase_id',
                                       string='Frases FEL')