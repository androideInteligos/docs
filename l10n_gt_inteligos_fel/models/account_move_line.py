# -*- coding: utf-8 -*-

from odoo.models import Model
from odoo.fields import Float


class AccountMoveLineInherited(Model):
    _inherit = "account.move.line"
    _name = "account.move.line"

    another_discount = Float(string="Otros Descuentos")
