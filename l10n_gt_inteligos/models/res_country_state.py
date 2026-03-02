# -*- coding: utf-8 -*-

from odoo.models import Model
from odoo.fields import Many2one, Char


class InheritResCountryState(Model):
    """Herencia al Objeto res.country.state para agregarle
        el campo sub_region_id para la relación con una sub-región.
    """
    _inherit = 'res.country.state'

    sub_region_id = Many2one(comodel_name="gt.sub_region", string="Sub-región")
    gt_code = Char('Code')
