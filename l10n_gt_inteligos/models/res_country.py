# -*- coding: utf-8 -*-

from odoo.models import Model
from odoo.fields import Text
from odoo import _
from odoo.api import model, constrains
from odoo.exceptions import UserError


class CountryInherit(Model):
    """Herencia al Objeto res.country para la sobre escritura de campo address_format para cambiar
        el formato de dirección en los reportes y cómo aparece la dirección de cada contacto.
    """
    _inherit = 'res.country'

    @model
    def _get_default_address_format(self):
        """Sobreescritura de método genérico de obtener e formato predeterminado de dirección
            para modificar el formato agregando el campo municipio en lugar del genérico city.
        """
        return "%(street)s\n%(street2)s\n%(county_name)s, %(state_code)s,\n%(country_name)s"

    address_format = Text(string="Formato en Reportes",
                                 help="Display format to use for addresses belonging to this country.\n\n"
                                      "You can use python-style string pattern with all the fields of the address "
                                      "(for example, use '%(street)s' to display the field 'street') plus"
                                      "\n%(county_name)s: the name of the county"
                                      "\n%(state_name)s: the name of the state"
                                      "\n%(state_code)s: the code of the state"
                                      "\n%(country_name)s: the name of the country"
                                      "\n%(country_code)s: the code of the country",
                                 default=lambda self: self._get_default_address_format())

    @constrains('address_format')
    def _check_address_format(self):
        """Sobreescritura de método genérico para verificar la existencia
            de los campos del formato predeterminado de dirección
            para modificarlo agregando el campo municipio en lugar del genérico ´city´.
        """
        for record in self:
            if record.address_format:
                address_fields = self.env['res.partner']._formatting_address_fields() + ['county_name', 'state_code',
                                                                                         'state_name', 'country_code',
                                                                                         'country_name', 'company_name']
                try:
                    record.address_format % {i: 1 for i in address_fields}
                except (ValueError, KeyError):
                    raise UserError(_('The layout contains an invalid format key'))
