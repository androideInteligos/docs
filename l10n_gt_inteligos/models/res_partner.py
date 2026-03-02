# -*- coding: utf-8 -*-

import requests
from xml.etree.ElementTree import fromstring, ElementTree

from odoo import fields, api, models
from odoo.exceptions import ValidationError
from odoo.tools import config


class ResPartnerInherited(models.Model):
    _inherit = 'res.partner'

    legal_name = fields.Char(string="Razón Social")
    vat = fields.Char(string="NIT", default='CF')
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.company
    )
    property_account_payable_id = fields.Many2one(
        comodel_name='account.account',
        default=lambda self: self.env['account.account'].search(
            [('account_type', '=', 'liability_payable'),
             ('deprecated', '=', False),
             ('company_ids', 'in', self.env.company.id)],
            limit=1, order='code asc')
    )
    property_account_receivable_id = fields.Many2one(
        comodel_name='account.account',
        default=lambda self: self.env['account.account'].search(
            [('account_type', '=', 'asset_receivable'),
             ('deprecated', '=', False),
             ('company_ids', 'in', self.env.company.id)],
            limit=1, order='code asc')
    )

    # G_territorial_division fields
    county_id = fields.Many2one(
        'gt.county',
        ondelete="set null",
        store=True,
        copy=False,
        domain="[('state_id', '=?', state_id)]",
        string="Municipio",
        index=True,
        help='Ingrese el municipio para la dirección del cliente.'
    )
    sub_region_id = fields.Many2one(
        comodel_name="gt.sub_region",
        related='state_id.sub_region_id',
        depends=['state_id', 'state_id.sub_region_id'],
        store=True, string="Sub-región"
    )
    region_id = fields.Many2one(
        comodel_name="gt.region",
        related='state_id.sub_region_id.region_id',
        depends=['state_id', 'state_id.sub_region_id'],
        store=True, string="Región"
    )
    zone_partner_id = fields.Many2one(
        comodel_name="gt.zone",
        ondelete="set null",
        copy=False,
        string="Zone"
    )

    @api.constrains('vat')
    def _check_vat_unique(self):
        if self.env.company.account_fiscal_country_id.code == 'GT':
            for record in self:
                duplicate_nit = record.env.company.duplicate_nit

                if record.parent_id or not record.vat or record.vat == 'CF':
                    continue
                test_condition = (config['test_enable'] and not self.env.context.get('test_vat'))
                if test_condition:
                    continue
                results = self.env['res.partner'].search_count([
                    ('parent_id', '=', False),
                    ('vat', '=', record.vat),
                    ('legal_name', '=', record.legal_name),
                    ('id', '!=', record.id),
                    ('company_id', '=', record.env.company.id),
                    ('country_id', '=', record.country_id.id)
                ])

                if results and not duplicate_nit:
                    raise ValidationError("El número de NIT %s ya existe." + record.vat)

    @api.model
    def search_legal_name_by_nit(self, nit, name):
        """Consulta de razón social por medio de NIT ingresado.
                Verificación de la razón social en el servicio web de la SAT.
            """
        if nit != 'CF' and self.env.company.account_fiscal_country_id.code == 'GT':
            url = 'https://consultareceptores.feel.com.gt/rest/action'
            headers = {'Content-Type': 'application/json'}
            data = {
                "emisor_codigo": '101529643',
                "emisor_clave": 'CEFD1D3A74F08D2A3979CAB404DF1E59',
                "nit_consulta": nit.replace("-", "")
            }
            resp = requests.post(url=url, json=data, headers=headers)
            result = resp.json()
            if result.get('mensaje'):
                raise ValidationError(result['mensaje'])

            raw_name = result.get('nombre')
            if raw_name:
                legal_name = " ".join(part for part in raw_name.split(',') if part.strip())
            else:
                legal_name = name

            return legal_name

    @api.onchange('vat')
    def _onchange_vat(self):
        # changegt
        if self.env.company.account_fiscal_country_id.code == 'GT':

            if not self.vat == 'CF' and self.l10n_latam_identification_type_id.is_vat:
                if self.vat:
                    legal_name = self.search_legal_name_by_nit(self.vat, self.name)
                    self.legal_name = legal_name
                else:
                    raise ValidationError('Valor ingresado para NIT no es válido. Ingréselo un NIT por favor.')

    def write(self, vals):
        """Herencia al método genérico write para llenar el campo razón social
            en los contactos que no tienen razón social ingresada"""
        # changegt
        if self.env.company.account_fiscal_country_id.code == 'GT':

            for record in self:
                if not record.legal_name and not vals.get('legal_name', False):
                    vals['legal_name'] = record.browse(record.parent_id.id).legal_name or record.browse(
                        record.parent_id.id).name \
                        if record.parent_id else record.name
        res = super(ResPartnerInherited, self).write(vals)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Actualización del 15.07.2021
            Herencia realizada para mejorar el método create,
             para asignarle la razón social de la empresa padre si tuviere contacto padre,
             caso contrario colocar el nombre ingresado como razón social.
        """
        # changegt
        if self.env.company.account_fiscal_country_id.code == 'GT':
            for vals in vals_list:
                if not vals.get('legal_name', False):
                    vals['legal_name'] = self.browse(vals['parent_id']).legal_name \
                        if vals.get('parent_id', False) else vals.get('name', 'Ingresar una razón social.')
        res = super(ResPartnerInherited, self).create(vals_list)
        return res

    # gt_territorial_division methods
    @api.onchange('county_id')
    def _onchange_county(self):
        if self.env.company.account_fiscal_country_id.code == 'GT':
            if self.county_id:
                self.country_id = self.county_id.state_id.country_id.id \
                    if self.county_id.state_id and self.county_id.state_id.country_id else False
                self.state_id = self.county_id.state_id.id if self.county_id.state_id else False

    @api.model
    def _address_fields(self):
        """Herencia de método para agregar nuevo campo 'county' a los campos de dirección."""
        result = super(ResPartnerInherited, self)._address_fields()
        if self.filtered(lambda x: x.country_code == 'GT'):
            result + ['county_id']
        return result

    def _prepare_display_address(self, without_company=False):
        """Herencia del método para agregar nuevo valor a los args 'county_name' para el formato de dirección."""
        address_format, args = super(ResPartnerInherited, self)._prepare_display_address(without_company)
        if self.env.company.account_fiscal_country_id.code == 'GT':
            args.update({'county_name': self.county_id.name})
            for key in args.keys():
                if not args.get(key, False):
                    address_format.replace('%(' + key + ')s,', '%(' + key + ')s')
        return address_format, args

    @api.model
    def default_get(self, fields_list):
        """Herencia del método para que al crear un nuevo contacto este tenga Guatemala como país por defecto"""
        res = super().default_get(fields_list)
        if not self._context.get('default_country_id') and 'country_id' in fields_list:
            company = self.env.company
            if company and company.account_fiscal_country_id:
                if self.env.company.account_fiscal_country_id.code == 'GT': # remover esta línea para que aplique a cualquier país asignado a la compañía
                    res['country_id'] = company.account_fiscal_country_id.id
        return res