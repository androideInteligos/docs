# -*- coding: utf-8 -*-

from odoo.models import Model
from odoo.fields import (Char, One2many)

# ----------------------------------------------------------
# gt_territorial_division
# ----------------------------------------------------------
class GTRegion(Model):
    """Objeto para los registros regiones geográficas Guatemala
        que serán necesarios y útiles para uso en filtros de vistas y reportes.
        Agruparán las sub-regiones según la configuración de los usuarios Administrativos.
    """
    _name = 'gt.region'
    _description = 'Región geográfica de Guatemala'

    name = Char(string="Nombre")
    sub_region_ids = One2many(
        comodel_name="gt.sub_region",
        inverse_name="region_id",
        string="Sub-regiones"
    )
    description = Char(string="Descripción")
