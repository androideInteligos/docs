# -*- coding: utf-8 -*-

from odoo.fields import Char
from odoo.models import Model


class IdentificationTypeInherited(Model):
    _inherit = 'l10n_latam.identification.type'
    _name = 'l10n_latam.identification.type'

    key_name_fel = Char(string="Nombre FEL de identificación")
