# -*- coding: utf-8 -*-

from odoo import models, fields


class FelUrls(models.Model):
    _name = 'company.fel_url'
    _description = 'Urls FEL'

    company_id = fields.Many2one(
        comodel_name='res.company',
        readonly=True,
        default=lambda self: self.env.company.id,
        string='Compañía'
    )
    use_type = fields.Selection(
        selection=[
            ('sign', 'Firmar'),
            ('certify', 'Certificar'),
            ('cancel', 'Anular'),
            ('token', 'Token'),
            ('unique_number', 'Correlativo'),
        ],
        required=True, default="certify",
        string='Uso', help="El uso seleccionado será para el cual se usarán las urls."
    )
    prod_url = fields.Char(
        default="La url para comunicación en pruebas debe ser ingresada acá.",
        help="La url para comunicación en producción debe ser ingresada acá.",
        string='Url-Producción'
    )
    test_url = fields.Char(
        default="La url para comunicación de pruebas debe ser ingresada acá.",
        help="La url para comunicación en producción debe ser ingresada acá.",
        string='Url-pruebas'
    )
