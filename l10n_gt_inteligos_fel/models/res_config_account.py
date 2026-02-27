# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigAccountInherited(models.TransientModel):
    _inherit = "res.config.settings"
    _name = "res.config.settings"

    mandatory_address_fel = fields.Boolean(
        store=True,
        index=True,
        related="company_id.mandatory_address_fel",
        readonly=False,
        string="¿Ingresar direcciones FEL?",
    )
    amount_restrict_cf = fields.Float(
        string='Monto restrictivo',
        related="company_id.amount_restrict_cf",
        readonly=False,
        help="Este campo es útil para almacenar el monto restrictivo "
             "para emisiones FEL con identificación de cliente CF"
    )
