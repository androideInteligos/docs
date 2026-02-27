# -*- coding: utf-8 -*-

from odoo.models import Model
from odoo.fields import Float


class SaleOrderLineInherited(Model):
    _inherit = "sale.order.line"
    _name = "sale.order.line"

    another_discount = Float(string="Otros Descuentos")
