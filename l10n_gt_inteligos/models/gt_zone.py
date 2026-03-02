# -*- coding: utf-8 -*-

from odoo.models import Model
from odoo.fields import (Char, Many2one)


class GTZone(Model):
    """Objeto para los registros de zonas municipales geográficos Guatemala
        que serán necesarios y útiles en lugar de el campo genérico Odoo city.
        Serán agrupados en los respectivos departamentos.
    """
    _name = "gt.zone"
    _description = "Zonas Municipales de Guatemala"

    name = Char(
        store=True,
        index=True,
        copy=False,
        required=True,
        string="Nombre",
        help='Ingrese el nombre del municipio'
    )
    county_id = Many2one(
        comodel_name='gt.county',
        ondelete="set null",
        store=True,
        copy=False,
        string="Municipio",
        index=True,
        help='Ingrese el municipio al que pertenece la zona'
    )
    state_id = Many2one(
        'res.country.state',
        ondelete="set null",
        related='county_id.state_id',
    )
    country_id = Many2one(
        'res.country',
        ondelete="set null",
        related='state_id.country_id',
    )
    gt_code = Char(
        string="Codigo"
    )
