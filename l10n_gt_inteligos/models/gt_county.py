# -*- coding: utf-8 -*-

from odoo.models import Model
from odoo.fields import (Char, Many2one, One2many)

# ----------------------------------------------------------
# gt_territorial_division
# ----------------------------------------------------------
class GTCounty(Model):
    """Objeto para los registros municipios geográficos Guatemala
        que serán necesarios y útiles en lugar de el campo genérico Odoo city.
        Serán agrupados en los respectivos departamentos.
    """
    _name = "gt.county"
    _description = "Municipio geográfico de Guatemala"

    name = Char(
        store=True,
        index=True,
        copy=False,
        required=True,
        string="Nombre",
        help='Ingrese el nombre del municipio'
    )
    zone_ids = One2many(
        comodel_name='gt.zone',
        inverse_name='county_id',
        string='Zonas'
    )
    state_id = Many2one(
        comodel_name='res.country.state',
        ondelete="set null",
        store=True,
        string="Departamento",
        index=True,
    )
    country_id = Many2one(
        comodel_name='res.country',
        ondelete="set null",
        related='state_id.country_id',
        store=True,
        string="País",
        index=True,
    )
    gt_code = Char(
        string="Código"
    )
