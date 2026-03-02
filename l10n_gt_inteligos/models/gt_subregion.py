# -*- coding: utf-8 -*-

from odoo.models import Model
from odoo.fields import (Char, Many2one, One2many)


class GTSubRegion(Model):
    """Objeto para los registros sub-regiones geográficas Guatemala
        que serán necesarios y útiles para uso en filtros de vistas y reportes.
        Agruparán departamentos según la configuración de los usuarios Administrativos.
    """
    _name = 'gt.sub_region'
    _description = 'Sub-región geográfica de Guatemala'

    name = Char(string="Nombre")
    region_id = Many2one(comodel_name="gt.region", string="Región")
    state_ids = One2many(
        comodel_name="res.country.state",
        inverse_name="sub_region_id",
        domain="[('country_id.code', '=', 'GT')]",
        string="Departamentos"
    )
    description = Char(string="Descripción")
