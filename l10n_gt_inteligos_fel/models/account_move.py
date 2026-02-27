# -*- coding: utf-8 -*-

from re import sub
from math import trunc
from uuid import uuid4
from datetime import datetime
from logging import getLogger
from pytz import timezone, UTC
from dateutil.parser import parse

import hashlib
import time
import requests
from psycopg2 import (Error, DatabaseError, OperationalError, InternalError)
from xml.etree.ElementTree import fromstring, ElementTree

from ..providers.infile import InfileFel, emisor, receptor
from ..providers.digifact import DigifactFel, DigifactEmisor, DigifactReceptor
from ..providers.contap import ContapFel, ContapEmisor, ContapReceptor
from ..providers.megaPrint import MegaPrintFel, MegaPrintEmisor, MegaPrintReceptor
from ..providers.ecofacturas import EcofacturaFel, EcofacturaEmisor, EcofacturaReceptor
from ..providers.eForcon import eForconFel, eForconEmisor, eForconReceptor

from odoo.tools.misc import format_date
from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext

_logger = getLogger(__name__)

PAYMENT_METHODS = {
    "e": "Efectivo",
    "c": "Cheque",
    "t": "Transferencia",
    "tc": "Tarjeta de Crédito",
    "de": "Depósito",
    "cr": "Credito"
}


class FELLog(models.Model):
    _name = "account.move.fel_log"
    _description = 'Bitácora FEL'

    response = fields.Char(string="Respuesta", required=True, readonly=True)
    type = fields.Selection(
        selection=[
            ("S", "Satisfactorio"),
            ("E", "Error")
        ], required=True,
        string="Tipo", readonly=True
    )
    timestamp = fields.Datetime("Fecha", required=True, readonly=True)
    error_msg = fields.Char("Mensaje Error", readonly=True)
    source = fields.Char("Fuente", readonly=True)
    category = fields.Char("Categoria", readonly=True)
    numeral = fields.Char("Numeral", readonly=True)
    validation = fields.Char("Validacion", readonly=True)
    account_move_id = fields.Many2one("account.move", required=True, readonly=True)
    contingency_id = fields.Many2one("account.fel_contingency", readonly=True)


class FELContingency(models.Model):
    _name = "account.fel_contingency"
    _description = 'Contingencias FEL'

    date_start = fields.Datetime(string="Fecha y Hora Inicio", required=True, readonly=True, copy=False)
    date_end = fields.Datetime(string="Fecha y Hora Fin", readonly=True, copy=False)
    location = fields.Char(string="Numero Establecimiento", readonly=True, copy=False)
    source = fields.Char(string="Motivo", required=True, copy=False)
    documents_qty = fields.Integer(string="Cantidad Documentos", copy=False)
    logs = fields.One2many(comodel_name="account.move.fel_log", inverse_name="contingency_id",
                           string="Bitácoras FEL", readonly=True, copy=False)
    move_ids = fields.One2many(comodel_name="account.move", inverse_name="contingency_id", string="DTEs")

    @api.depends('move_ids')
    def compute_docs_qty(self):
        for record in self:
            record.documents_qty = len(record.move_ids)


class AccountMoveReversalInherited(models.TransientModel):
    """Mejora para agregar tipo de documento rectificativo en el wizard"""
    _inherit = "account.move.reversal"
    _name = "account.move.reversal"

    @api.model
    def _doc_type_domain(self):
        return [
            ('id', 'in', (self.env.ref('l10n_gt_td_generic.dc_ncre').id, self.env.ref('l10n_gt_td_generic.dc_ndeb').id,
                          self.env.ref('l10n_gt_td_generic.dc_nabn').id))
        ]

    dte_to_note_id = fields.Many2one("account.move", string="DTE para hacer Nota")
    dte_doc_type = fields.Many2one(
        comodel_name='l10n_latam.document.type',
        string='Tipo Documento', copy=False,
        domain=_doc_type_domain
    )

    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversalInherited, self)._prepare_default_reversal(move)
        res['dte_to_note_id'] = self.dte_to_note_id.id or move.id
        res['reason_note'] = self.reason or " "
        res['pos_inv'] = False
        res['invoice_doc_type'] = self.dte_doc_type.id
        return res


class AccountMoveInherited(models.Model):
    _inherit = "account.move"
    _name = "account.move"

    def compute_total_amount(self):
        for record in self:
            # total = sum([line.line_total for line in record.invoice_line_ids])
            # record.amount = total

            tdp_amout_tax = 0
            invoice_totals = record.tax_totals

            if invoice_totals:
                amounts_by_group = {}

                for amount_by_group_list in invoice_totals['groups_by_subtotal'].values():

                    for amount_by_group in amount_by_group_list:
                        amounts_by_group = {
                            amount_by_group['tax_group_name']: amount_by_group['tax_group_amount']
                        }
                    tdp_amout_tax += amounts_by_group.get('TIMBRE DE PRENSA', 0)
            total = sum([line.line_total for line in record.invoice_line_ids])
            record.amount = total + tdp_amout_tax

    @api.depends('invoice_date', 'company_id.tax_lock_date')
    def _compute_dont_cancel_move(self):
        """Método computado para calcular qué facturas pueden o no pueden ser canceladas
            según la fecha de cada una con respecto a la fecha de cierre contable de impuestos.
            Restringir a todas las facturas con fecha igual o anterior a la fecha establecida para el bloqueo.
            Restringir la visualización del botón de Anulación en las 
            facturas cuando ya se haya excedido la fecha del pago del IVA de las facturas. 
        """

        for record in self.with_context(prefetch_fields=False):
            tax_lock_date = record.company_id.tax_lock_date
            record.dont_cancel_move = bool(
                record.invoice_date <= tax_lock_date) if tax_lock_date and record.invoice_date else False

    def _compute_can_edit_data_fel(self):
        self.can_edit_data_fel = self.env.user.has_group('l10n_gt_inteligos_fel.group_fel_manager')

    @api.depends('partner_id', 'partner_shipping_id', 'company_id')
    def _compute_fiscal_position_id(self):
        """Override del método para priorizar la posición fiscal del pedido si está disponible
        """
        for move in self:
            if move.invoice_origin:
                sale_order = self.env['sale.order'].search([('name', '=', move.invoice_origin)], limit=1)
                if sale_order and sale_order.fiscal_position_id:
                    move.fiscal_position_id = sale_order.fiscal_position_id
                    continue
            super(AccountMoveInherited, move)._compute_fiscal_position_id()

    amount = fields.Monetary(compute="compute_total_amount", string="Suma total")
    state = fields.Selection(
        selection_add=[
            ('contingency', 'Contingencia')
        ], ondelete={'contingency': 'cascade'}, string='Estado',
    )
    pos_inv = fields.Boolean(states={'posted': [('readonly', True)]}, default=False, store=True,
                             string="Factura POS", copy=False)
    can_edit_data_fel = fields.Boolean(compute='_compute_can_edit_data_fel',
                                       store=True, string="Puede editar datos FEL")
    error_serialization = fields.Boolean(states={'posted': [('readonly', True)]}, default=False,
                                         store=True, string="Error de serialización", copy=False)
    process_fel = fields.Boolean(states={'posted': [('readonly', True)]}, default=False,
                                 store=True, string="FEL en proceso", copy=False)
    contingency_id = fields.Many2one(comodel_name="account.fel_contingency", readonly=True, copy=False)
    key_identifier = fields.Char(string="Identificador Único", copy=False, tracking=100,
                                 help="Este campo puede ser alfanumérico de 32 caracteres, "
                                      "sirve como identificador único de los documentos "
                                      "eletrónicos del emisor, para evitar duplicidad de los mismos.")
    validate_internal_reference = fields.Selection(
        states={'posted': [('readonly', True)]},
        selection=[('VALIDAR', 'VALIDAR'), ('NO_VALIDAR', 'NO VALIDAR')],
        default="VALIDAR",
        help="Este campo puede ser usado para momentos de contingencia en donde sea necesario emitir un DTE, "
             "aunque no se tenga acceso a internet. "
             "Lo cual hará que DIGIFACT almacene este documento para ser emitido en un máximo de 5 días despues.",
        copy=False,
        string="Validar Documento por Contingencia"
    )

    doc_xml_generated = fields.Char(states={'posted': [('readonly', True)]}, string='XML Generado', copy=False)
    certify_xml = fields.Char(states={'posted': [('readonly', True)]}, string='XML Certificado', copy=False)
    signed_xml = fields.Char(states={'posted': [('readonly', True)]}, string='XML Firmado', copy=False)
    fel_uuid = fields.Char(string="UUID", copy=False)
    fel_serie = fields.Char(string="Serie FEL", copy=False)
    fel_number = fields.Char(string="Número FEL", copy=False)
    fel_date = fields.Char(string="Fecha FEL", copy=False)
    fel_num_acceso = fields.Char(string="Numero Acceso FEL", readonly=True, copy=False)
    fel_logs = fields.One2many(comodel_name="account.move.fel_log",
                               inverse_name="account_move_id", string="Bitácora FEL",
                               readonly=True, copy=False, tracking=3)

    ancient_regime = fields.Boolean(states={'posted': [('readonly', True)]},
                                    string="Régimen Antiguo", default=False, copy=False)
    date_ancient_regime = fields.Char(store=True, copy=False, states={'posted': [('readonly', True)]},
                                      string="Fecha de Régimen Antiguo")
    series_ancient_regime = fields.Char(store=True, copy=False, states={'posted': [('readonly', True)]},
                                        string="Serie de Régimen Antiguo")
    doc_ancient_regime = fields.Char(store=True, copy=False, states={'posted': [('readonly', True)]},
                                     string="# Doc Régimen Antiguo")
    uuid_ancient_regime = fields.Char(store=True, copy=False, states={'posted': [('readonly', True)]},
                                      string="# Autorización de Régimen Antiguo")

    reason_note = fields.Char(states={'posted': [('readonly', True)]}, string="Motivo Ajuste", default=' ', copy=False)
    dte_to_note_id = fields.Many2one(comodel_name="account.move", states={'posted': [('readonly', True)]},
                                     string="DTE para Nota", copy=False)

    date_dte_to_refund = fields.Char(related="dte_to_note_id.fel_date", string="Fecha de DTE para NCRE")
    series_dte_to_refund = fields.Char(related="dte_to_note_id.fel_serie", string="Serie de DTE para NCRE")
    number_dte_to_refund = fields.Char(related="dte_to_note_id.fel_number", string="Número de DTE para NCRE")
    uuid_dte_to_refund = fields.Char(related="dte_to_note_id.fel_uuid", string="UUID de DTE para NCRE")

    doc_xml_cancel_generated = fields.Char(states={'posted': [('readonly', True)]},
                                           string='XML Cancelación Generado', copy=False)
    certify_cancel_xml = fields.Char(states={'posted': [('readonly', True)]},
                                     string='XML Cancelación Certificado', copy=False)
    signed_cancel_xml = fields.Char(states={'posted': [('readonly', True)]},
                                    string='XML Cancelación Firmado', copy=False)
    fel_uuid_cancel = fields.Char(string="UUID Anulacion", readonly=True, copy=False)
    fel_series_cancel = fields.Char(string="Serie FEL Anulacion", readonly=True, copy=False)
    fel_number_cancel = fields.Char(string="Numero FEL Anulacion", readonly=True, copy=False)
    fel_date_cancel = fields.Char(string="Fecha FEL Anulacion", readonly=True, copy=False)
    fel_num_acceso_cancel = fields.Char(string="Numero Acceso FEL Anulacion", readonly=True, copy=False)

    #######--------------------Campos de contacto inmutables luego de emisión-------------------#####
    street = fields.Char(states={'posted': [('readonly', True)]}, string='Dirección Calle del contacto')
    street2 = fields.Char(states={'posted': [('readonly', True)]}, string='Dirección Calle 2 del contacto')
    email = fields.Char(states={'posted': [('readonly', True)]}, string='Correo')
    zip = fields.Char(states={'posted': [('readonly', True)]}, change_default=True, string='Código postal del contacto')
    county_id = fields.Many2one(states={'posted': [('readonly', True)]}, comodel_name='gt.county',
                                domain="[('state_id', '=?', state_id)]",
                                string="Municipio del contacto", ondelete="restrict")
    state_id = fields.Many2one(states={'posted': [('readonly', True)]}, comodel_name="res.country.state",
                               string='Departamento del contacto', ondelete='restrict',
                               domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one(states={'posted': [('readonly', True)]}, comodel_name="res.country",
                                 string='País del contacto', ondelete='restrict')
    dont_cancel_move = fields.Boolean(compute='_compute_dont_cancel_move', default=False,
                                      store=True, string="Don't cancel the move", copy=False)
    expedition_place = fields.Char(string="Lugar de Expedición")
    consignee_country = fields.Char(string="País Consignatario")

    # def _track_subtype(self, init_values):
    #     self.ensure_one()
    #
    #     if self.is_sale_document(include_receipts=False) and self.env.company.its_fel:
    #
    #         if self.id and 'key_identifier' in init_values:
    #             init_values.update({'process_fel': True})
    #     return super(AccountMoveInherited, self)._track_subtype(init_values)

    def _check_parallel_diff_records(self):
        # update_date = self._context[self.CONCURRENCY_CHECK_FIELD]  # TODO: sin uso de momento.
        query = "SELECT id FROM account_move WHERE process_fel = True GROUP BY id, write_date HAVING (now() - write_date) <= INTERVAL '0 years 0 months 0 days 0 hours 0 minutes 10 seconds 100 milliseconds'"
        self.env.cr.execute(query)
        result = self.env.cr.fetchall()
        target_record_ams = list(map(lambda b: self.env['account.move'].browse(b[0]), result))

        if target_record_ams:
            return target_record_ams
        else:
            return False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        Herencia del método propio de Odoo para agregar lógica que permita obtener desde los documentos
        fiscales y contables el valor de los campos dirección de calle, dirección de calle 2,
        código postal, municipio, departamento y país del contacto seleccionado.
        :return: None o alerta del tipo 'warning'
        """
        result = super(AccountMoveInherited, self)._onchange_partner_id()

        if self.state == 'draft' and self.partner_id:
            self.write({'street': self.partner_id.street, 'street2': self.partner_id.street2,
                        'zip': self.partner_id.zip, 'email': self.partner_id.email,
                        'county_id': self.partner_id.county_id.id if self.partner_id.county_id else False,
                        'state_id': self.partner_id.state_id.id if self.partner_id.state_id else False,
                        'country_id': self.partner_id.country_id.id if self.partner_id.country_id else False})

        if result:
            return result

    def truncate(self, number, decimals=0):
        factor = 10.0 ** decimals
        return trunc(number * factor) / factor

    def create_message_data_fel(self, response_fel):
        """
        Mejora para obtención de tipo de documento para chatter.
        """
        dte_type = self._get_sequence().l10n_latam_document_type_id.doc_code_prefix

        if dte_type.strip() not in ['NCRE', 'NDEB']:
            doc = 'Factura'
        elif dte_type.strip() == 'NDEB':
            doc = 'Nota de Débito'
        else:
            doc = 'Nota de Crédito'

        if self.state == 'posted':
            doc = 'Anulación ' + doc

        uuid = response_fel["uuid"] or self.fel_uuid
        series = response_fel["serie"] or self.fel_serie
        number = str(response_fel["numero"]) or self.fel_number
        display_msg = """<b>Datos """ + doc + """ FEL:</b> 
                         <br/> 
                          <ul>
                              <li>UUID: """ + uuid + """</li>
                              <li>Serie FEL: """ + series + """</li>
                              <li>Numero FEL: """ + number + """</li>
                              <li>Fecha FEL: """ + response_fel["fecha"] + """</li>
                              <li>Numero Acceso FEL: </li>
                          </ul> 
                          <br/>"""
        if self.state == 'draft' and self.company_id.fel_provider == 'IN':
            display_msg += """<a href='https://report.feel.com.gt/ingfacereport/ingfacereport_documento?uuid=""" + \
                           response_fel[
                               "uuid"] + """' target='_blank'>Aquí puede visualizar el formato INFILE del documento emitido.</a>"""
        elif self.state == 'draft' and self.company_id.fel_provider == 'FC':
            display_msg += """<a href='""" + \
                           response_fel[
                               "ruta_PDF"] + """' target='_blank'>Aquí puede visualizar el formato eFORCON del documento emitido.</a>"""
        elif self.state == 'draft' and self.company_id.fel_provider == 'DI': #TODO: Solo funciona para el ambiente de producción
            display_msg += """<a href='https://felgtaws.digifact.com.gt/guest/api/FEL?DATA=""" + self.company_id.vat + '|' + \
                           response_fel[
                               "uuid"] + '|' + 'GUESTUSERQR' + """' target='_blank'>Aquí puede visualizar el formato DIGIFACT del documento emitido.</a>"""
        followers = self.message_partner_ids.ids
        odoobot = self.env.ref('base.partner_root')
        self.message_post(body=display_msg, message_type='notification', subject="Datos FEL",
                          partner_ids=followers, starred=True, author_id=odoobot.id)

    def manage_contingency(self, move, response_fel):
        if move.state == 'draft':
            move.state = 'contingency'
            instance_contingency = self.env['account.fel_contingency']
            contingency = instance_contingency.search([('date_end', '=', False)])

            if not contingency:
                """Pensar sobre esto"""
                loc = ''
                contingency_values = {
                    'date_start': fields.Datetime.now(), 'location': loc,
                    'source': response_fel["descripcion"],
                    'move_ids': [(1, move.id, {'name': move.name})]
                }
                instance_contingency.create(contingency_values)
            elif contingency and contingency.filtered(lambda c: c['move_ids'] not in move.id):
                contingency.move_ids += [(1, move.id, {'name': move.name})]

    def void_contingency(self, contingency):
        for move in contingency.move_ids:
            if move.state == 'contingency':
                move.action_post()

    def response_dte_fel(self, response_fel, xml_generated, certify_xml, signed_xml, fel_uuid, fel_date,
                         fel_series, fel_number, account_move_id):
        for move in self:
            result = response_fel.get("resultado", False)
            instance_contingency = self.env['account.fel_contingency']
            instance_log = self.env['account.move.fel_log']
            gt = timezone('America/Guatemala')
            utc_dt = datetime.now(tz=UTC).astimezone(gt)
            date = utc_dt.strftime('%Y-%m-%d %H:%M:%S')

            if result:
                move[xml_generated] = response_fel["xml_plano"]
                move[certify_xml] = response_fel["xml_certificado"]
                move[signed_xml] = response_fel["xml_firmado"]
                move[fel_uuid] = response_fel["uuid"]
                move[fel_date] = response_fel["fecha"]
                move[fel_series] = response_fel["serie"]
                move[fel_number] = str(response_fel["numero"])

                try:
                    move.create_message_data_fel(response_fel)
                except Exception as e:
                    obj_log = {
                        'response': tools.ustr(e),
                        'type': 'E', 'timestamp': date,
                        'error_msg': tools.ustr(e),
                        'source': 'Odoo-Certificador',
                        'category': 'ERROR AL OBTENER REPORTE FEL',
                        'numeral': '#',
                        'validation': '',
                        'account_move_id': account_move_id
                    }
                    instance_log.create(obj_log)

                #  ACTUALIZACION UTIL PARA CONTINGENCIAS
                if move.state == 'contingency':
                    move.state = 'draft'

                    contingency = instance_contingency \
                        .search([('date_end', '=', False), ('move_ids', 'in', move.id)])
                    if contingency:
                        contingency.date_end = fields.Datetime.now()

                    #  AQUI LLAMAR AL METODO PARA VACIAR LA CONTINGENCIA
                    #  REVISAR DETENIDAMENTE EL PROCESO, YA QUE TIENE FALLOS
                    move.void_contingency(contingency)
                    #  AQUI LLAMAR AL METODO PARA VACIAR LA CONTINGENCIA
                #  ACTUALIZACION UTIL PARA CONTINGENCIAS

                if response_fel.get('pdf', False):
                    self.env['ir.attachment'].create({
                        'name': f"PDF de emisión FEL {move.key_identifier}",
                        'type': 'binary',
                        'datas': response_fel['pdf'],
                        'store_fname': "PDF de emisión FEL",
                        'res_model': move._name,
                        'res_id': move.id,
                        'mimetype': 'application/x-pdf'
                    })
                return True

            else:
                move[xml_generated] = response_fel["xml_plano"]

                if response_fel.get('descripcion_errores', False):  # Espera una lista
                    self.env.user.notify_danger(message='No fue posible emitir el documento, '
                                                        'tómate un tiempo para revisar en la sección de abajo ---> '
                                                        '***Datos FEL*** lo que ha ocurrido.')

                    for error_fel in response_fel['descripcion_errores']:
                        obj_log = {
                            'response': response_fel["descripcion"],
                            'type': 'E', 'timestamp': date,
                            'error_msg': error_fel["mensaje_error"],
                            'source': error_fel["fuente"],
                            'category': error_fel["categoria"],
                            'numeral': error_fel["numeral"],
                            'validation': error_fel["validacion"],
                            'account_move_id': account_move_id
                        }

                        #  ACTUALIZACION UTIL PARA CONTINGENCIAS AUN FALTA
                        #  REVISAR
                        log = instance_log.create(obj_log)
                        contingency = instance_contingency.search([('date_end', '=', False)])
                        if contingency and response_fel.get('access_number'):
                            contingency.logs += [(1, log.id, {'error_msg': log.error_msg})]
                    if response_fel.get('access_number'):
                        move.manage_contingency(move, response_fel)
                        move[fel_uuid] = response_fel["access_number"]

                    elif move.pos_inv:
                        raise ValidationError(
                            'La emisión de DTE no pudo ser realizada por errores ocurridos. '
                            'Favor revisar los registros de errores FEL '
                            'ERROR: ' +
                            response_fel['descripcion_errores'][0]["mensaje_error"] +
                            ' XML: ' + response_fel.get('xml_plano')
                        )
                    #  ACTUALIZACION UTIL PARA CONTINGENCIAS AUN FALTA
                    return False
                else:
                    #  ACTUALIZACION UTIL PARA CONTINGENCIAS AUN FALTA
                    if response_fel.get('access_number'):
                        move.manage_contingency(move, response_fel.get('sign_response'))
                    else:
                        raise ValidationError(
                            response_fel.get('descripcion', '') + ' ' +
                            str(response_fel.get('sign_response', '')) +
                            ' XML: ' + response_fel.get('xml_plano', '')
                        )
                #  ACTUALIZACION UTIL PARA CONTINGENCIAS

    def data_notes(self, doc):
        note = ''
        dte_id = self.dte_to_note_id
        date_dte = self.date_dte_to_refund
        uuid_dte = self.uuid_dte_to_refund
        series_dte = self.series_dte_to_refund
        doc_dte = self.number_dte_to_refund

        if doc == 'NCRE':
            note = 'Crédito'
        elif doc == 'NDEB':
            note = 'Débito'

        if self.ancient_regime:
            data_to_ncre = [self.series_ancient_regime, self.uuid_ancient_regime, self.date_ancient_regime]

            for data in data_to_ncre:

                if not data:
                    raise ValidationError('No puedes hacer la Nota de ' + note + ' para el régimen '
                                                                                 'antiguo, pues hay campos '
                                                                                 'obligatorios sin datos.')
            fel_date = parse(self.date_ancient_regime).strftime("%Y-%m-%d")
            uuid = self.uuid_ancient_regime
            series = self.series_ancient_regime
            doc_dte = self.doc_ancient_regime
            return {
                'fel_date': fel_date,
                'uuid': uuid,
                'series': series,
                'doc_dte': doc_dte
            }
        else:

            if dte_id:
                fel_date = parse(date_dte).strftime("%Y-%m-%d")
                return {
                    'fel_date': fel_date,
                    'uuid': uuid_dte,
                    'series': series_dte,
                    'doc_dte': doc_dte
                }
            else:
                raise ValidationError('No existe un documento FEL para el que '
                                      'deseas hacer una Nota de ' + note + '.')

    # Actualización para validar nit desde el POS
    def validate_nit(self, nit, name):
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

    def tax(self, taxable_unit_code, taxable_amount, tax_amount):
        return {
            'taxable_unit_code': taxable_unit_code,
            'taxable_amount': taxable_amount,
            'tax_amount': tax_amount
        }

    def set_key_identifier(self, dte_doc_type=False):

        if self.company_id.fel_provider == "MP":
            identifier = "-".join(str(uuid4()).split("-")).upper()
        elif self.company_id.fel_provider == "ECO":
            identifier = self.company_id.get_doc_identifier(dte_doc_type)
        else:
            hash_sha = hashlib.sha1()
            hash_sha.update(str(time.time()).encode('utf-8'))
            identifier = hash_sha.hexdigest()[:32]
        return identifier

    def examine_values(self, values, factor):
        values_evaluated = {}

        for key, val in values.items():

            if val:

                if self.env.company.fel_provider != 'DI':
                    values_evaluated[key] = val.strip().replace("&", "&amp;").replace("'", "&apos;"). \
                        replace(">", "&gt;").replace('"', "&quot;").replace('ñ', "&#241;").replace('Ñ', "&#209;") \
                        .replace('á', "&#225;").replace('é', "&#233;").replace('í', "&#237;") \
                        .replace('ó', "&#243;").replace('ú', "&#250;").replace('Á', "&#193;") \
                        .replace('É', "&#201;").replace('Í', "&#205;") \
                        .replace('Ó', "&#211;").replace('Ú', "&#218;") \
                        if key.upper() != 'NIT' else val.replace("-", "")
                else:
                    values_evaluated[key] = val.strip().replace("&", "&amp;").replace("'", "&apos;"). \
                        replace(">", "&gt;").replace('"', "&quot;").replace('<', "&lt;")
            else:
                raise ValidationError('Falta llenar campo ' + key + ' en ' + factor)
        return values_evaluated

    def remove_tildes(self, value):
        mapa_tildes = {
            'á': 'a', 'Á': 'A', 'é': 'e', 'É': 'E', 'í': 'i', 'Í': 'I',
            'ó': 'o', 'Ó': 'O', 'ú': 'u', 'Ú': 'U', ':': ''
        }
        return ''.join(mapa_tildes.get(char, char) for char in value)

    def set_description_item(self, line):
        """
        Método útil para obtener el valor para la descripción de cada línea de factura a emitir.
        :param line: instancia de línea de factura.
        :return: diccionario con el valor estandarizado según caracteres especiales.
        """
        return self.examine_values({'description': line.name or line.display_name}, 'líneas de factura')

    def set_items(self, export, exempt, t, dte_type, provider, company, certify_fel_dte, precision_rounding):
        """
        Método necesario para el cálculo y adición de valores respectivos a las líneas de cada factura.
        :param export: valor boleano para verificar sobre exportaciones.
        :param exempt: valor boleano para verificar sobre exenciones.
        :param t: diccionario de valores genéricos de impuestos.
        :param dte_type: cadena de caracteres con el nombre corto del tipo de documento a emitir.
        :param provider: instancia del objeto de la clase del certificador usado para emitir.
        :param company: instancia del objeto de la compañía para la que se desea emitir el DTE.
        :param certify_fel_dte: instancia de la librería del certificador usado para emitir.
        :param precision_rounding: valor entero para truncar los montos decimales enviados al certificador.
        :return: un valor flotante que representa al monto total de impuestos y 2 listas de valores de impuestos y
                 valores para validaciones al emitir DTEs de exportaciones sin incoterm.
        """
        tax_total = 0.00
        taxes = list()
        result = list()
        data_base_taxes = {k: 0.00 for k in t.keys()}
        service_type_products = list()

        def merge_t_values(list_dictionary):
            """Función para unir los montos de impuestos en las líneas de factura."""
            for d in list_dictionary:
                data_base_taxes.update({k: data_base_taxes[k] + v for k, v in d.items() if k != 'taxable_unit_code'})

        for idx, line in enumerate(self.invoice_line_ids.
                                           filtered(lambda l: l.display_type not in ['line_section', 'line_note'])):
            item = provider.item()
            item.set_numero_linea(idx + 1)
            goods_service = 'B'

            if line.product_id.type == 'service':
                goods_service = 'S'
                service_type_products.append(goods_service)
            elif line.product_id.type == 'consu' or line.product_id.type == 'product':
                goods_service = 'B'
            item.set_bien_o_servicio(goods_service)
            item.set_cantidad(line.quantity)
            item.set_unidad_medida(line.product_id.uom_id.name)
            description_sanitized = self.set_description_item(line)
            description = description_sanitized.get('description')
            pattern = r'^/'
            description_reformat = sub(pattern, '', description)
            item.set_descripcion(description_reformat)
            item.set_precio_unitario(self.truncate(line.price_unit, precision_rounding))
            # Descuentos
            desc = (line.price_unit * line.quantity) * (line.discount / 100)
            price = line.line_total + desc
            item.set_descuento(self.truncate(desc, precision_rounding))
            """Mejora para envio de tipo de impuesto TIMBRE DE PRENSA"""
            """RECORDATORIO, CAMBIOS metodo compute_total_amount ARCHIVO account_move.py"""
            amount_tax = line.tax_ids.filtered(lambda tax: tax.tax_group_id.name == 'TIMBRE DE PRENSA').amount
            taxable_price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxable_amount = taxable_price_unit * line.quantity / 1.12
            sum_tax = (amount_tax * taxable_amount) / 100

            if company.fel_provider != 'FC':
                item.set_precio(self.truncate(price, precision_rounding))  # a este no aplicar el descuento
                item.set_total(self.truncate(line.line_total + sum_tax or 0.0, precision_rounding))
            else:
                amount_tax = line.tax_ids.filtered(lambda tax: tax.name == 'TASA MUNICIPAL').amount

                if amount_tax:
                    item.set_tasamunicipal(float(amount_tax))

            # no aplica para Notas de Abono ni para Recibos, ni recibo por donación
            if dte_type.strip() not in ['NABN', 'RECI', 'RDON'] and company.fel_provider != 'FC':

                for tax in line.tax_ids:
                    tax_item = provider.impuesto()

                    if tax.tax_group_id:
                        tax_short_name = tax.tax_group_id.name

                        if tax_short_name == 'IVA':

                            if company.fel_iva == 'GEN':

                                """Exentos"""
                                if export or exempt:
                                    t = self.tax(2, self.truncate(line.line_total, precision_rounding), 0)
                                else:
                                    taxable_amount = self.truncate(
                                        abs(line.price_unit * line.quantity - desc) / (1 + (tax.amount / 100)),
                                        precision_rounding)
                                    t = self.tax(1, taxable_amount,
                                                 self.truncate((tax.amount * taxable_amount) / 100, precision_rounding))
                            elif company.fel_iva == 'PEQ' and dte_type.strip() != 'FESP' or company.fel_iva == 'EXE':
                                t = self.tax(2, self.truncate(line.line_total, precision_rounding), 0)
                            elif company.fel_iva == 'PEQ' and dte_type.strip() == 'FESP':
                                taxable_amount = self.truncate(
                                    abs(line.price_unit * line.quantity - desc) / (1 + (tax.amount / 100)),
                                    precision_rounding)
                                t = self.tax(1, taxable_amount,
                                             self.truncate((tax.amount * taxable_amount) / 100, precision_rounding))
                        elif tax_short_name == 'RETENCIONES':
                            continue
                        elif tax_short_name == 'IDP':
                            continue
                        elif tax_short_name == 'TIMBRE DE PRENSA':

                            if company.fel_iva == 'GEN':
                                taxable_amount = abs(line.price_unit * line.quantity - desc) / 1.12
                                t = self.tax(1, self.truncate(taxable_amount, precision_rounding),
                                             self.truncate((tax.amount * taxable_amount) / 100, precision_rounding))
                            elif company.fel_iva == 'PEQ' or company.fel_iva == 'EXE':
                                t = self.tax(2, self.truncate(line.line_total, precision_rounding), 0)
                        else:
                            raise ValidationError('El impuesto en la(s) línea(s) tiene grupo'
                                                  ' de impuestos no permitido.')
                        tax_total += t['tax_amount']
                        tax_item.set_monto_gravable(t['taxable_amount'])
                        tax_item.set_monto_impuesto(t['tax_amount'])
                        tax_item.set_codigo_unidad_gravable(t['taxable_unit_code'])
                        tax_item.set_nombre_corto(tax_short_name)
                        item.set_impuesto(tax_item)

                        """Mejora para envio de más de un tipo de impuesto"""
                        if tax_short_name not in [tax_values['tax'] for tax_values in taxes]:
                            taxes.append({'tax': tax_short_name, 'total_tax': t['tax_amount']})
                        else:
                            for tax_values in taxes:

                                if tax_short_name == tax_values['tax']:
                                    tax_values['total_tax'] += t['tax_amount']
                        result.append(t)
                    else:
                        raise ValidationError('El impuesto en la(s) línea(s) no tiene grupo de impuestos.')
            # no aplica para Notas de Abono ni para Recibos, ni recibo por donación
            """Mejora para agregar nombre corto de impuesto de línea para proveedor FEL Eforcon"""
            if company.fel_provider == 'FC':  # TODO: Realizar la revisión para los distintos impuestos. eForcon

                for tax in line.tax_ids:

                    if tax.name == 'TASA MUNICIPAL':
                        item.set_nombre_corto_impuesto("TASA MUNICIPAL")
                        taxable_amount = taxable_price_unit * line.quantity / 1.12
                        sum_tax = (tax.amount * taxable_amount) / 100
                        name = tax.gt_state_id.gt_code + tax.gt_county_id.gt_code + '000-' + str(
                            round(float(sum_tax), 2))
                        item.set_tasamunicipal(name)
                        break
                    else:
                        item.set_nombre_corto_impuesto(tax.name)

                if export or exempt:
                    item.set_nombre_corto_impuesto('IVA (EXENTO)')

            certify_fel_dte.agregar_item(item)
        merge_t_values(result)
        del data_base_taxes['taxable_unit_code']
        return taxes, tax_total, data_base_taxes, service_type_products

    def _validate_establishment_configuration(self):
        journal = self.journal_id
        if all([journal.establishment_name, journal.establishment_number, journal.street, journal.county_id,
                journal.state_id, journal.zip_code, journal.country_id]):
            return True
        elif any([journal.establishment_name, journal.establishment_number, journal.street, journal.county_id,
                  journal.state_id, journal.zip_code, journal.country_id]):
            raise ValidationError(
                "¡Algunos campos de la configuración del Establecimiento en el Diario están incompletos!")
        else:
            return False

    def dte_fel(self):
        move = self
        _logger.info("ESTAS DENTRO DE EMISIONES FEL!")
        instance_company = move.company_id
        instance_partner = move.partner_id
        total_amount = move.amount

        if move.currency_id != instance_company.currency_id:
            total_amount = move.amount * move.rate_invoice

        if (total_amount >= instance_company.amount_restrict_cf) and instance_partner.vat == 'CF':
            raise ValidationError('Según Acuerdo Gubernativo No. 245-2022 y '
                                  'la Resolución de Superintendencia SAT DSI-1350-2022, '
                                  'una factura con valores mayores o iguales a Q. 2500.00 '
                                  'no puede tener identificación CF, '
                                  'por favor haga la corrección y pruebe emitir nuevamente. '
                                  'Puede ingresar un NIT válido o un número de DPI.')

        precision_rounding = 10

        if instance_company.fel_provider == 'IN':
            provider = InfileFel
            emisor_fel = emisor
            receptor_fel = receptor
        elif instance_company.fel_provider == 'DI':
            provider = DigifactFel
            emisor_fel = DigifactEmisor
            receptor_fel = DigifactReceptor
        elif instance_company.fel_provider == 'CO':
            provider = ContapFel
            emisor_fel = ContapEmisor
            receptor_fel = ContapReceptor
        elif instance_company.fel_provider == "MP":
            provider = MegaPrintFel
            emisor_fel = MegaPrintEmisor
            receptor_fel = MegaPrintReceptor
        elif instance_company.fel_provider == "ECO":
            provider = EcofacturaFel
            emisor_fel = EcofacturaEmisor
            precision_rounding = 6
            receptor_fel = EcofacturaReceptor
        elif instance_company.fel_provider == "FC":
            provider = eForconFel
            emisor_fel = eForconEmisor
            receptor_fel = eForconReceptor
        else:
            raise ValidationError('No ha seleccionado a ningún proveedor para la emisión FEL. '
                                  'Debe ser configurado en la compañía emisora. '
                                  'Por favor hágalo o comuníquese con administración.')

        # Metodos principales de librerias FEL según cada proveedor
        certify_fel_dte = provider.fel_dte()
        emisor_fel = emisor_fel.emisor()
        receptor_fel = receptor_fel.receptor()

        # Variables para emisor y receptor
        factor = 'compañía'
        establishment_code = instance_company.establishment_number
        street = False
        zip_code = False
        city = False
        state = False
        country = False
        name = False
        receptor_name = False
        receptor_street = False
        receptor_city = False
        receptor_state = False
        receptor_country = False
        receptor_zip = False
        receptor_email = False
        receptor_email_cc = False

        if move.pos_inv:
            """Evalúa si es una factura proveniente del punto de venta para obtener los datos del establecimiento
            en la configuración del PoS"""
            po_order = self.env['pos.order'].search([('account_move', '=', move.id)], limit=1)

            if po_order:
                instance_config_po = po_order.session_id.config_id
                street = instance_config_po.street
                zip_code = instance_config_po.zip_code
                city = instance_config_po.county_id.name
                state = instance_config_po.state_id.name
                country = instance_config_po.country_id.code
                name = instance_config_po.name
                establishment_code = str(instance_config_po.establishment_number)
                factor = 'punto de venta'
                receptor_name = self.validate_nit(instance_partner.vat, instance_partner.name) \
                    if (instance_partner.vat != 'CF' and instance_partner.l10n_latam_identification_type_id.is_vat) \
                    else instance_partner.legal_name or instance_partner.name
                instance_partner.legal_name = receptor_name
                receptor_street = instance_partner.street or 'Guatemala'
                # receptor_city = instance_partner.county_id.name if instance_partner.county_id else ' ' TODO: Mejora para el POS
                receptor_city = instance_partner.city if instance_partner.city else ' '
                receptor_state = instance_partner.state_id.name or ' '
                receptor_country = instance_partner.country_id.code or 'GT'
                receptor_zip = instance_partner.zip or '00000'
                receptor_email = instance_partner.email or ' '
                receptor_email_cc = instance_partner.invoice_email or instance_partner.email
        elif self._validate_establishment_configuration():
            """Si es una factura no proveniente del PoS evalúa primero los datos del establecimiento en el Diario"""
            street = move.journal_id.street
            zip_code = move.journal_id.zip_code
            city = move.journal_id.county_id.name
            state = move.journal_id.state_id.name
            country = move.journal_id.country_id.code
            name = move.journal_id.establishment_name
            establishment_code = str(move.journal_id.establishment_number)
            factor = 'diario'
            receptor_name = self.validate_nit(instance_partner.vat, instance_partner.name) \
                if (instance_partner.vat != 'CF' and instance_partner.l10n_latam_identification_type_id.is_vat) \
                else instance_partner.legal_name or instance_partner.name
            instance_partner.legal_name = receptor_name
            receptor_street = instance_partner.street or 'Guatemala'
            receptor_city = instance_partner.city if instance_partner.city else ' '
            receptor_state = instance_partner.state_id.name or ' '
            receptor_country = instance_partner.country_id.code or 'GT'
            receptor_zip = instance_partner.zip or '00000'
            receptor_email = instance_partner.email or ' '
            receptor_email_cc = instance_partner.invoice_email or receptor_email
        else:
            street = instance_company.street
            zip_code = instance_company.zip
            city = instance_company.county_id.name
            state = instance_company.state_id.name
            country = instance_company.country_id.code
            name = instance_company.name
            receptor_name = instance_partner.legal_name.strip() if move.legal_name else False
            receptor_email = instance_partner.email or ' '
            receptor_email_cc = instance_partner.invoice_email or receptor_email

            if not instance_company.fel_provider == "MP":
                receptor_email = move.email or ' '

            """ Mejora para agregar lógica de configuración para el ingreso de direcciones FEL.
-                    Obligatoria o no, en dependencia de la configuración de Contabilidad."""
            if not instance_company.mandatory_address_fel:

                if move.invoice_incoterm_id:  # TODO: FIX ME, fue una CHAPUZA.
                    receptor_street = instance_partner.street or '---'
                    receptor_city = instance_partner.county_id.name if instance_partner.county_id else '---'
                    receptor_state = instance_partner.state_id.name or '---'
                    receptor_country = instance_partner.country_id.code or '---'
                else:
                    receptor_street = instance_partner.street or 'Guatemala'
                    receptor_city = instance_partner.county_id.name if instance_partner.county_id else 'Guatemala'
                    receptor_state = instance_partner.state_id.name if instance_partner.state_id else 'Guatemala'
                    receptor_country = instance_partner.country_id.code if instance_partner.country_id else 'GT'
                receptor_zip = instance_partner.zip or '00000'
            else:
                receptor_street = instance_partner.street
                receptor_city = instance_partner.county_id.name if instance_partner.county_id else False
                receptor_state = instance_partner.state_id.name if instance_partner.state_id else False
                receptor_country = instance_partner.country_id.code if instance_partner.country_id else False
                receptor_zip = instance_partner.zip

        # Datos dirección emisor
        direction_values_emisor = {
            'Calle': street, 'Código Postal': zip_code,
            'Municipio': city, 'Departamento': state,
            'País': country
        }
        vde = self.examine_values(direction_values_emisor, factor)

        #  Datos dirección Receptor
        direction_values_receptor = {
            'Calle': receptor_street, 'Código Postal': receptor_zip,
            'Municipio': receptor_city, 'Departamento': receptor_state,
            'País': receptor_country
        }
        vdr = self.examine_values(direction_values_receptor, 'cliente')

        if instance_company.fel_provider not in ["ECO", "FC"]:
            emisor_fel.set_direccion(vde['Calle'], vde['Código Postal'], vde['Municipio'], vde['Departamento'],
                                     vde['País'])

        data_values_emisor = {  # Datos Emisor
            'Fel Iva': instance_company.fel_iva, 'Correo': instance_company.email,
            'Nit': instance_company.vat, 'Nombre Comercial': name,
            'Razón Social': instance_company.legal_name
        }
        dve = self.examine_values(data_values_emisor, factor)
        """Mejora para envío de datos si el cliente es un consumidor final."""

        if instance_partner.its_final_consumer:
            receptor_name = 'Consumidor Final'
        """--------Fin Actualización 22/04/2021-----------"""
        data_values_receptor = {
            'Correo': receptor_email, 'Nit': instance_partner.vat,
            'Razón Social': receptor_name, 'Correo CC': receptor_email_cc,
        }
        dvr = self.examine_values(data_values_receptor, 'cliente')

        if instance_company.fel_provider not in ["FC"]:
            emisor_fel.set_datos_emisor(dve['Fel Iva'], establishment_code, dve['Correo'],
                                        dve['Nit'], dve['Nombre Comercial'], dve['Razón Social'])
            receptor_fel.set_direccion(vdr['Calle'], vdr['Código Postal'], vdr['Municipio'], vdr['Departamento'],
                                       vdr['País'])
            receptor_fel.set_datos_receptor(dvr['Correo'], dvr['Nit'], dvr['Razón Social'])
        else:
            emisor_fel = eForconEmisor.emisor()
            emisor_fel.set_datos_emisor(dve['Nit'], establishment_code)
            receptor_fel = eForconReceptor.receptor()
            receptor_type = instance_partner.l10n_latam_identification_type_id.key_name_fel

            if move.invoice_doc_type.doc_code_prefix.strip() == 'FESP':
                receptor_type = 'C'
            receptor_fel.set_datos_receptor(dvr['Nit'], dvr['Razón Social'], dvr['Correo'], dvr['Correo CC'],
                                            vdr['Calle'], vdr['Código Postal'], vdr['Municipio'],
                                            vdr['Departamento'], vdr['País'], tipo_receptor=receptor_type)
        certify_fel_dte.set_datos_emisor(emisor_fel)
        certify_fel_dte.set_datos_receptor(receptor_fel)

        gt = timezone('America/Guatemala')
        utc_dt = datetime.now(tz=UTC).astimezone(gt)
        custom_dt = datetime.combine(move.invoice_date, datetime.min.time()) \
            if move.invoice_date and move.invoice_date < fields.Date.today() else False
        dt = utc_dt if not custom_dt else custom_dt

        dtime_emission = False

        if instance_company.fel_provider in ['IN', 'MP']:
            dtime_emission = dt.strftime("%Y-%m-%dT%H:%M:%S") + '-06:00'
        elif instance_company.fel_provider in ['DI', 'CO']:
            dtime_emission = dt.strftime("%Y-%m-%dT%H:%M:%S")
        elif instance_company.fel_provider in ['ECO', 'FC']:
            dtime_emission = dt.strftime("%Y-%m-%d")

        if move.journal_id:
            if move.invoice_doc_type == move._get_sequence().l10n_latam_document_type_id:
                dte_type = move._get_sequence().l10n_latam_document_type_id.doc_code_prefix
            else:
                raise ValidationError(
                    'La secuencia del diario seleccionado no concuerda con el tipo de documento a emitir.'
                )
        else:
            raise ValidationError('No tienes un diario seleccionado.')
        certify_fel_dte.set_datos_generales(move.currency_id.name, dtime_emission, dte_type.strip())

        # # identificador unico del dte del cliente
        identifier = move.name

        if not move.key_identifier:
            identifier = self.set_key_identifier(dte_type.strip())
            move.key_identifier = identifier
        elif move.key_identifier:

            if self.company_id.fel_provider == "ECO":
                identifier = self.set_key_identifier(dte_type.strip())
            else:
                identifier = move.key_identifier
        certify_fel_dte.set_clave_unica(identifier)

        if move.state == 'contingency' and instance_company.fel_provider != 'ECO':  # USO PARA CONTINGENCIAS
            if dte_type.strip() == 'NCRE':
                access_number = move.fel_num_acceso_ncre
            elif dte_type.strip() == 'NDEB':
                access_number = move.fel_num_acceso_ndeb
            else:
                access_number = move.fel_num_acceso
            certify_fel_dte.set_acceso(access_number)

        export = ''
        exempt = False
        # agregar las frases
        phrases = dict()

        def set_phrase(phrase, type_phrase, resolution_number, resolution_date):
            if str(type_phrase) == '4' and \
                    dte_type.strip() in ['FACT', 'FCAM', 'NCRE', 'NDEB', 'FESP', 'RECI', 'RDON']:  # Exentos
                certify_fel_dte.frase_fel.set_frase(str(phrase), str(type_phrase))
                exp = "SI" if str(phrase) == '1' else ''  # indicador de las frases exportacion
                certify_fel_dte.set_exportacion(exp)
                return True, exp
            elif str(type_phrase) in ('1', '2', '8', '9') and \
                    dte_type.strip() in ['FACT', 'FCAM', 'NCRE', 'NDEB']:
                if resolution_number and resolution_date:
                    certify_fel_dte.frase_fel.set_frase(str(phrase), str(type_phrase), str(resolution_number),
                                                        str(resolution_date))
                else:
                    certify_fel_dte.frase_fel.set_frase(str(phrase), str(type_phrase))
                return False, ''
            elif str(type_phrase) == '3' and dte_type.strip() in ['FPEQ',
                                                                  'FCAP',
                                                                  'FAPE']:  # TODO: falta agregar tipos de documento 11 al 16.
                certify_fel_dte.frase_fel.set_frase(str(phrase), str(type_phrase))
                return False, ''
            elif str(type_phrase) == '5' and dte_type.strip() == 'FESP':
                certify_fel_dte.frase_fel.set_frase(str(phrase), str(type_phrase))
                return False, ''
            elif str(
                    type_phrase) == '6' and dte_type.strip() != 'NABN':  # TODO: falta agregar tipos de documento 11 al 16.
                certify_fel_dte.frase_fel.set_frase(str(phrase), str(type_phrase))
                return False, ''
            elif str(
                    type_phrase) == '7' and dte_type.strip() not in ['NABN',
                                                                     'FESP']:  # TODO: falta agregar tipos de documento 11 al 16.
                if resolution_number and resolution_date:
                    certify_fel_dte.frase_fel.set_frase(str(phrase), str(type_phrase), str(resolution_number),
                                                        str(resolution_date))
                else:
                    certify_fel_dte.frase_fel.set_frase(str(phrase), str(type_phrase))
                return False, ''
            elif str(type_phrase) == '8' and dte_type.strip() in ['RECI', 'RDON']:
                certify_fel_dte.frase_fel.set_frase(str(phrase), str(type_phrase))
                return False, ''
            elif str(type_phrase) == '9' and dte_type.strip() in ['FPEQ', 'FCAP']:
                certify_fel_dte.frase_fel.set_frase(str(phrase), str(type_phrase))
                return False, ''
            else:
                return False, ''

        def set_phrases(iter_phrases):
            exempts, exports = list(), list()

            for ph in iter_phrases:

                if ph.phrase not in phrases.keys() or phrases.get(ph.phrase, False) != ph.type:
                    phrases.update({ph.phrase: ph.type})
                    exe, exp = set_phrase(ph.phrase, ph.type, ph.resolution_number, ph.resolution_date)
                    exempts.append(exe)
                    exports.append(exp)
            return any(exempts), any(exports)

        """Cambios 25.10.2022 para agregar frases exportación a tipo NCRE de exportación 
            Deben estar presentes según actualización SAT v1.7.3, 
            probado en reunión con Allan Bonilla de Digifact"""
        if move.fiscal_position_id:
            exempt, export = set_phrases(move.fiscal_position_id.fel_phrases_ids)
        elif instance_partner.fel_phrases_ids:
            exempt, export = set_phrases(instance_partner.fel_phrases_ids)

        if move.journal_id.fel_phrases_ids:
            set_phrases(move.journal_id.fel_phrases_ids)
        elif instance_company.fel_phrases_ids:
            set_phrases(instance_company.fel_phrases_ids)

        if instance_company.fel_provider == 'ECO':

            if instance_partner.l10n_latam_identification_type_id.is_vat:  # TODO: por si acaso se fuera a utilizar en un futuro, en caso de los demás certificadores no aplica.
                especial_type = "1"
            elif instance_partner.l10n_latam_identification_type_id.key_name_fel == 'EXT':
                especial_type = "3"
            else:
                especial_type = "2"
        else:
            especial_type = instance_partner.l10n_latam_identification_type_id.key_name_fel

        if not instance_partner.l10n_latam_identification_type_id.is_vat and instance_company.fel_provider != 'FC':
            certify_fel_dte.set_tipo_especial(especial_type)
        elif instance_company.fel_provider == 'ECO':
            certify_fel_dte.set_tipo_especial(especial_type)

        t = move.tax(1, 0.00, 0.00)
        taxes, tax_total, t, service_type_products = move.set_items(export, exempt, t, dte_type, provider,
                                                                    instance_company, certify_fel_dte,
                                                                    precision_rounding)

        if instance_company.fel_provider not in ["ECO", "FC"]:
            # Totales
            total_fel = provider.totales()
            total_fel.set_gran_total(self.truncate(move.amount, precision_rounding))
            # no aplica para Notas de Abono ni para Recibos, ni recibo por donación

            if dte_type.strip() not in ['NABN', 'RECI', 'RDON']:

                for tax in taxes:
                    taxes_total = provider.total_impuesto()
                    taxes_total.set_nombre_corto(tax['tax'])
                    taxes_total.set_total_monto_impuesto(self.truncate(tax['total_tax'], precision_rounding))
                    total_fel.set_total_impuestos(taxes_total)
                # no aplica para Notas de Abono ni para Recibos, ni recibo por donación
            certify_fel_dte.agregar_totales(total_fel)

        if instance_company.fel_provider == 'IN':

            if instance_company.adendas_ids:

                for adenda in instance_company.adendas_ids:
                    """Mejora para permitir que las adendas sean enviadas segun tipo de documento o sin tipo definido.
                        Si no se ha definido tipo, las adendas serán para cualquier tipo de doc,
                        si se ha definido tipo de documento, se evaluara que sea el mismo tipo de la emision.
                        caso contrario, no se enviaran las adendas."""

                    if not adenda.doc_type_id:
                        access = True
                    elif adenda.doc_type_id.doc_code_prefix.strip() == dte_type.strip():
                        access = True
                    else:
                        access = False
                    if access:
                        # # agregar adendas al gusto
                        fel_adenda = InfileFel.adenda()

                        fel_adenda.nombre = adenda.name
                        if adenda.model_id != 'account.move':
                            if adenda.model_id == 'res.partner':
                                fel_adenda.valor = str(move.partner_id[adenda.field_id.name]) if move.partner_id[adenda.field_id.name] else ''
                            elif adenda.model_id == 'res.users':
                                fel_adenda.valor = str(move.user_id[adenda.field_id.name]) if move.user_id[adenda.field_id.name] else ''
                            elif adenda.model_id == 'res.company':
                                fel_adenda.valor = str(move.company_id[adenda.field_id.name]) if move.company_id[adenda.field_id.name] else ''
                            elif adenda.model_id == 'account.payment.term':
                                fel_adenda.valor = str(move.invoice_payment_term_id[adenda.field_id.name]) if move.invoice_payment_term_id[adenda.field_id.name] else ''
                            elif adenda.model_id == 'sale.order':
                                for line in move.invoice_line_ids:
                                    order = line.sale_line_ids.mapped('order_id')
                                    if order:
                                        if adenda.field_id.name == 'partner_id':
                                            value = str(order.partner_id.name) \
                                                if order.partner_id.company_type == 'person' else ''
                                            fel_adenda.valor = value
                                        elif adenda.field_id.name == 'picking_ids':
                                            value = ''
                                            for pick in order.picking_ids:
                                                value += str(pick.name)
                                            fel_adenda.valor = value
                                        else:
                                            fel_adenda.valor = str(order[adenda.field_id.name]) if order[adenda.field_id.name] else ''
                                    else:
                                        """Quitar el warning fue necesario debido a que 
                                            no alertaba de nada, nunca aparecia esto, 
                                            y no permitia la emision del documento con FEL, solo en odoo.
                                            A cambio coloqué fel_adenda.valor = ''"""
                                        fel_adenda.valor = ''
                            elif adenda.model_id == 'product.template':
                                product_adendas = ''
                                for idx, line in enumerate(move.invoice_line_ids):
                                    product_adendas += str(idx + 1) + " @ " \
                                                       + str(line.product_id[adenda.field_id.name]) + " | "
                                fel_adenda.valor = product_adendas
                        else:
                            if adenda.field_id.ttype == 'many2one':
                                fel_adenda.valor = str(move[adenda.field_id.name].name) if move[adenda.field_id.name].name else ''
                            elif adenda.field_id.name == 'display_name':
                                sequence = move._get_sequence()
                                number = '%%0%sd' % sequence.padding % \
                                         sequence._get_current_sequence().number_next_actual
                                name = '%s%s' % (sequence.prefix or '', number)
                                fel_adenda.valor = name
                            elif adenda.field_id.ttype == 'html':
                                fel_adenda.valor = html2plaintext(move[adenda.field_id.name]) if move[adenda.field_id.name] else ''
                            else:
                                fel_adenda.valor = str(move[adenda.field_id.name]) if move[adenda.field_id.name] else ''
                        certify_fel_dte.agregar_adenda(fel_adenda)
        elif instance_company.fel_provider == 'DI':
            # # agregar adendas al gusto
            fel_adenda = DigifactFel.adenda()
            fel_adenda.internal_reference = identifier
            fel_adenda.reference_date = dtime_emission
            fel_adenda.validate_internal_reference = move.validate_internal_reference
            certify_fel_dte.agregar_adenda(fel_adenda)
        elif instance_company.fel_provider == 'ECO':
            # # agregar adendas al gusto
            for idx, adenda in enumerate(instance_company.adendas_ids):

                if not adenda.doc_type_id:
                    access = True
                elif adenda.doc_type_id.doc_code_prefix.strip() == dte_type.strip():
                    access = True
                else:
                    access = False

                if access:
                    fel_adenda = EcofacturaFel.adenda()
                    concatenate_name_value = '0' if 0 < idx + 1 < 10 else ''
                    fel_adenda.name = 'TrnCampAd' + concatenate_name_value + str(idx + 1)
                    if adenda.model_id != 'account.move':
                        if adenda.model_id == 'res.partner':
                            fel_adenda.value = str(move.partner_id[adenda.field_id.name]) if move.partner_id[adenda.field_id.name] else ''
                        elif adenda.model_id == 'res.users':
                            fel_adenda.value = str(move.user_id[adenda.field_id.name]) if move.user_id[adenda.field_id.name] else ''
                        elif adenda.model_id == 'res.company':
                            fel_adenda.value = str(move.company_id[adenda.field_id.name]) if move.company_id[adenda.field_id.name] else ''
                        elif adenda.model_id == 'account.payment.term':
                            fel_adenda.value = str(move.invoice_payment_term_id[adenda.field_id.name]) if move.invoice_payment_term_id[adenda.field_id.name] else ''
                        elif adenda.model_id == 'sale.order':
                            for line in move.invoice_line_ids:
                                order = line.sale_line_ids.mapped('order_id')
                                if order:
                                    if adenda.field_id.name == 'partner_id':
                                        value = str(order.partner_id.name) \
                                            if order.partner_id.company_type == 'person' else ''
                                        fel_adenda.value = value
                                    else:
                                        fel_adenda.value = str(order[adenda.field_id.name]) if order[adenda.field_id.name] else ''
                                else:
                                    fel_adenda.value = ''
                        elif adenda.model_id == 'product.template':
                            product_adendas = ''
                            for idx, line in enumerate(move.invoice_line_ids):
                                product_adendas += str(idx + 1) + " @ " \
                                                   + str(line.product_id[adenda.field_id.name]) + " | "
                            fel_adenda.value = product_adendas
                    else:
                        if adenda.field_id.ttype == 'many2one':
                            fel_adenda.value = str(move[adenda.field_id.name].name) if move[adenda.field_id.name].name else ''
                        elif adenda.field_id.name == 'display_name':
                            sequence = move._get_sequence()
                            number = '%%0%sd' % sequence.padding % \
                                     sequence._get_current_sequence().number_next_actual
                            name = '%s%s' % (sequence.prefix or '', number)
                            fel_adenda.value = name
                        elif adenda.field_id.ttype == 'html':
                            fel_adenda.value = html2plaintext(move[adenda.field_id.name]) if move[adenda.field_id.name] else ''
                        else:
                            fel_adenda.value = str(move[adenda.field_id.name]) if move[adenda.field_id.name] else ''
                    certify_fel_dte.agregar_adenda(fel_adenda)
        elif instance_company.fel_provider == 'FC':
            # # agregar adendas al gusto
            for idx, adenda in enumerate(instance_company.adendas_ids):

                if not adenda.doc_type_id:
                    access = True
                elif adenda.doc_type_id.doc_code_prefix.strip() == dte_type.strip():
                    access = True
                else:
                    access = False

                if access:
                    fel_adenda = eForconFel.adenda()
                    concatenate_name_value = '0' if 0 < idx + 1 < 10 else ''
                    fel_adenda.nombre = adenda.name
                    if adenda.model_id != 'account.move':
                        if adenda.model_id == 'res.partner':
                            fel_adenda.valor = str(move.partner_id[adenda.field_id.name]) if move.partner_id[adenda.field_id.name] else ''
                        elif adenda.model_id == 'res.users':
                            fel_adenda.valor = str(move.user_id[adenda.field_id.name]) if move.user_id[adenda.field_id.name] else ''
                        elif adenda.model_id == 'res.company':
                            fel_adenda.valor = str(move.company_id[adenda.field_id.name]) if move.company_id[adenda.field_id.name] else ''
                        elif adenda.model_id == 'account.payment.term':
                            fel_adenda.valor = str(move.invoice_payment_term_id[adenda.field_id.name]) if move.invoice_payment_term_id[adenda.field_id.name] else ''
                        elif adenda.model_id == 'sale.order':
                            for line in move.invoice_line_ids:
                                order = line.sale_line_ids.mapped('order_id')
                                if order:
                                    if adenda.field_id.name == 'partner_id':
                                        value = str(order.partner_id.name) \
                                            if order.partner_id.company_type == 'person' else ''
                                        fel_adenda.valor = value
                                    else:
                                        fel_adenda.valor = str(order[adenda.field_id.name]) if order[adenda.field_id.name] else ''
                                else:
                                    fel_adenda.valor = ''
                        elif adenda.model_id == 'product.template':
                            product_adendas = ''
                            for idx, line in enumerate(move.invoice_line_ids):
                                product_adendas += str(idx + 1) + " @ " \
                                                   + str(line.product_id[adenda.field_id.name]) + " | "
                            fel_adenda.valor = product_adendas
                    else:

                        if adenda.field_id.ttype == 'many2one':
                            fel_adenda.valor = str(move[adenda.field_id.name].name) if move[adenda.field_id.name].name else ''
                        elif adenda.field_id.name == 'display_name':
                            sequence = move._get_sequence()
                            number = '%%0%sd' % sequence.padding % \
                                     sequence._get_current_sequence().number_next_actual
                            name = '%s%s' % (sequence.prefix or '', number)
                            fel_adenda.valor = name
                        elif adenda.field_id.ttype == 'html':
                            fel_adenda.valor = html2plaintext(move[adenda.field_id.name]) if move[adenda.field_id.name] else ''
                        else:
                            fel_adenda.valor = str(move[adenda.field_id.name]) if move[adenda.field_id.name] else ''
                    certify_fel_dte.agregar_adenda(fel_adenda)
        elif instance_company.fel_provider == 'MP':

            if instance_company.adendas_ids:

                for idx, adenda in enumerate(instance_company.adendas_ids):

                    if not adenda.doc_type_id:
                        access = True
                    elif adenda.doc_type_id.doc_code_prefix.strip() == dte_type.strip():
                        access = True
                    else:
                        access = False
                    if access:
                        # # agregar adendas al gusto
                        fel_adenda = MegaPrintFel.adenda()
                        fel_adenda.nombre = 'Valor' + str(idx + 1)

                        if adenda.model_id != 'account.move':
                            if adenda.model_id == 'res.partner':
                                fel_adenda.valor = str(move.partner_id[adenda.field_id.name]) if move.partner_id[adenda.field_id.name] else ''
                            elif adenda.model_id == 'res.users':
                                fel_adenda.valor = str(move.user_id[adenda.field_id.name]) if move.user_id[adenda.field_id.name] else ''
                            elif adenda.model_id == 'res.company':
                                fel_adenda.valor = str(move.company_id[adenda.field_id.name]) if move.company_id[adenda.field_id.name] else ''
                            elif adenda.model_id == 'account.payment.term':
                                fel_adenda.valor = str(move.invoice_payment_term_id[adenda.field_id.name]) if move.invoice_payment_term_id[adenda.field_id.name] else ''
                            elif adenda.model_id == 'sale.order':
                                for line in move.invoice_line_ids:
                                    order = line.sale_line_ids.mapped('order_id')
                                    if order:
                                        if adenda.field_id.name == 'partner_id':
                                            value = str(order.partner_id.name) \
                                                if order.partner_id.company_type == 'person' else ''
                                            fel_adenda.valor = value
                                        elif adenda.field_id.name == 'picking_ids':
                                            value = ''
                                            for pick in order.picking_ids:
                                                value += str(pick.name)
                                            fel_adenda.valor = value
                                        else:
                                            fel_adenda.valor = str(order[adenda.field_id.name]) if order[adenda.field_id.name] else ''
                                    else:
                                        """Quitar el warning fue necesario debido a que 
                                            no alertaba de nada, nunca aparecia esto, 
                                            y no permitia la emision del documento con FEL, solo en odoo.
                                            A cambio coloqué fel_adenda.valor = ''"""
                                        fel_adenda.valor = ''
                            elif adenda.model_id == 'product.template':
                                product_adendas = []

                                for line in move.invoice_line_ids:
                                    product_adendas.append(str(line.product_id[adenda.field_id.name]) if line.product_id[adenda.field_id.name] else '')
                                fel_adenda.valor = product_adendas
                        else:

                            if adenda.field_id.ttype == 'many2one':
                                fel_adenda.valor = str(move[adenda.field_id.name].name) if move[adenda.field_id.name].name else ''
                            elif adenda.field_id.name == 'display_name':
                                sequence = move._get_sequence()
                                number = '%%0%sd' % sequence.padding % \
                                         sequence._get_current_sequence().number_next_actual
                                name = '%s%s' % (sequence.prefix or '', number)
                                fel_adenda.valor = name
                            elif adenda.field_id.ttype == 'html':
                                fel_adenda.valor = html2plaintext(move[adenda.field_id.name]) if move[adenda.field_id.name] else ''
                            else:
                                fel_adenda.valor = self.remove_tildes(move[adenda.field_id.name]) if move[adenda.field_id.name] else ''

                                if adenda.field_id.ttype == 'selection':
                                    for payment in PAYMENT_METHODS:
                                        if payment == fel_adenda.valor:
                                            fel_adenda.valor = PAYMENT_METHODS.get(payment)

                        certify_fel_dte.agregar_adenda(fel_adenda)

        if dte_type == 'NCRE':
            """Mejora para cambiar el envío de posibles caracteres especiales en el campo motivo de ajuste
                   Mejora: ascii(move.reason_note) if isinstance(move.reason_note, str) else ascii('Anulación')
            """
            credit_notes_complement = provider.complemento_notas()
            data_notes = move.data_notes(dte_type.strip())
            reason_sanitized = move.examine_values(
                {'reason': move.reason_note if isinstance(move.reason_note, str) else 'Anulación'},
                'Nota de crédito')
            reason = reason_sanitized.get('reason')
            credit_notes_complement.agregar("ANTIGUO" if move.ancient_regime else "",
                                            reason, data_notes['fel_date'],
                                            data_notes['series'], data_notes['uuid'], data_notes['doc_dte'])
            certify_fel_dte.agregar_complemento(credit_notes_complement)
        elif dte_type.strip() == 'FCAM':
            """Mejora para agregar proveedor FEL eForcon, 
                ya que el esquema de este proveedor no recibe monto de abono, 
                ellos lo calculan internamente, 
                aunque sí solicita los días entre abonos.
                Los demás proveedores sí lo solicitan.
            """
            if instance_company.fel_provider != 'FC':
                exchange_complement = provider.complemento_cambiaria()
                third_param = move.truncate(move.amount, precision_rounding)
            else:
                exchange_complement = provider.complemento_cambiaria()
                third_param = 15
            expiration_date = move.invoice_date_due
            exchange_complement.agregar(1, expiration_date, third_param)
            """-----Fin Actualización del 16.06.2021------"""
            certify_fel_dte.agregar_complemento(exchange_complement)
        elif dte_type == 'FESP' and instance_company.fel_provider != 'FC':
            """Mejora para agregar proveedor FEL eForcon, 
                ya que el esquema de este proveedor tiene complemento para FESP, 
                ellos lo calculan internamente, mediante los parámetros tipoReceptor = 'C' y el tipo de doc 'FESP'.
            """

            if instance_company.fel_provider != 'ECO':
                fesp_complement = provider.complemento_especial()
                """Mejora para cambiar porcentaje para calculo de ISR retenido, 
                    del 7 al 5%. Segun nueva instruccion SAT
                    Nueva reforma hecha por SAT según Decreto 10-2012."""
                isr_retencion = move.truncate(t['taxable_amount'] * (5 / 100), precision_rounding)
                """----------FIN-----------"""
                free_total = move.truncate(abs(t['taxable_amount'] - isr_retencion), precision_rounding)
                fesp_complement.agregar(isr_retencion, tax_total, free_total)
                certify_fel_dte.agregar_complemento(fesp_complement)
        elif dte_type.strip() == 'NDEB':
            debit_notes_complement = provider.complemento_notas()
            data_notes = move.data_notes(dte_type.strip())
            reason_sanitized = move.examine_values(
                {'reason': move.reason_note if isinstance(move.reason_note, str)
                else 'Anulación'}, 'Nota de débito')
            reason = reason_sanitized.get('reason')
            debit_notes_complement.agregar("ANTIGUO" if move.ancient_regime else "",
                                           reason, data_notes['fel_date'],
                                           data_notes['series'], data_notes['uuid'], data_notes['doc_dte'])
            certify_fel_dte.agregar_complemento(debit_notes_complement)

        if export and dte_type.strip() not in ('NCRE', 'NDEB', 'NABN'):

            if instance_company.fel_provider == 'ECO':
                receptor_fel.set_purchaser_code(instance_partner.ref if instance_partner.ref else False)
            export_complement = provider.complemento_exportacion()

            if not move.invoice_incoterm_id and (len(move.invoice_line_ids.filtered(
                    lambda l: l.display_type not in ['line_section', 'line_note'])) != len(service_type_products)):
                raise ValidationError('No puedes realizar una factura de exportación '
                                      'sin INCONTERM, llénalo en la factura.')

            if instance_company.fel_provider == 'IN':

                if not instance_company.exporter_code:
                    raise ValidationError('No puedes realizar una factura de exportación con INFILE'
                                          'sin Código de exportación del emisor.')

            if instance_company.fel_provider in ['IN', 'DI', 'MP']:

                if not move.partner_shipping_id:
                    raise ValidationError('No puedes realizar una factura de exportación '
                                          'sin los datos del consignatario de destino.')

                if move.partner_shipping_id:

                    if not move.partner_shipping_id.name:
                        raise ValidationError('No puedes realizar una factura de exportación '
                                              'sin el nombre del consignatario de destino.')
                    if not move.partner_shipping_id.street:
                        raise ValidationError('No puedes realizar una factura de exportación '
                                              'sin enviar la dirección del consignatario de destino.')

                if not instance_partner.ref:
                    raise ValidationError('No puedes realizar una factura de exportación '
                                          'sin los datos para el código de comprador.')

            export_complement.agregar(move.partner_shipping_id.name
                                      if move.partner_shipping_id and move.partner_shipping_id.name else '',
                                      move.partner_shipping_id.street
                                      if move.partner_shipping_id and move.partner_shipping_id.street else '',
                                      move.partner_shipping_id.ref
                                      if move.partner_shipping_id and move.partner_shipping_id.ref else '-',
                                      instance_partner.name, instance_partner.street, instance_partner.ref
                                      if instance_partner.ref else '-',
                                      move.invoice_origin, move.invoice_incoterm_id.code
                                      if move.invoice_incoterm_id else '',
                                      instance_company.legal_name, instance_company.exporter_code,
                                      move.expedition_place or '', move.consignee_country or '')
            certify_fel_dte.agregar_complemento(export_complement)

        certify_fel = False

        if instance_company.fel_provider in ['IN', 'ECO']:
            credentials = [instance_company.fel_pass, instance_company.fel_pass_sign,
                           instance_company.fel_user, instance_company.vat, instance_company.email]

            for credential in credentials:

                if not credential:
                    raise ValidationError('La compañía no está bien configurada para el proveedor INFILE. '
                                          'Hay campos sin datos.')

            certify_fel = certify_fel_dte.certificar(instance_company.fel_pass, instance_company.fel_pass_sign,
                                                     instance_company.fel_user,
                                                     instance_company.vat.replace("-", ""),
                                                     instance_company.email, instance_company)

        elif instance_company.fel_provider == 'DI':
            credentials = [instance_company.token, instance_company.vat_digifact]

            for credential in credentials:

                if not credential:
                    raise ValidationError('La compañía no está bien configurada para el proveedor DIGIFACT. '
                                          'Hay campos sin datos. Por favor revise.')
            certify_fel = certify_fel_dte.certificar(instance_company.token,
                                                     instance_company.vat_digifact, instance_company)

        elif instance_company.fel_provider in ['CO', 'MP']:

            if not instance_company.token:
                raise ValidationError('La compañía no está bien configurada para el proveedor CONTAP o MEGAPRINT'
                                      'Falta el Token de autenticación. Por favor revise.')
            certify_fel = certify_fel_dte.certificar(instance_company.token, instance_company)
        elif instance_company.fel_provider in ['FC']:

            for credential in [move.company_id.fel_user, move.company_id.fel_pass, move.company_id]:

                if not credential:
                    raise ValidationError('La compañía no está bien configurada para el proveedor eForcon. '
                                          'Hay campos sin datos. Por favor revise y vuelva a intentar emitir.')
            certify_fel = certify_fel_dte.certificar(move.company_id.fel_pass, move.company_id.fel_user,
                                                     move.company_id)

        try:
            certificate = move.response_dte_fel(certify_fel, 'doc_xml_generated', 'certify_xml',
                                                'signed_xml', 'fel_uuid', 'fel_date',
                                                'fel_serie', 'fel_number', move.id)
        except (InternalError, Error, DatabaseError, OperationalError) as d:
            msg_error = f"ERROR Odoo con FEL: {d}"
            _logger.error(msg_error)
            move.write({'error_serialization': True})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': f'Error de base de datos, por favor no publique de nuevo el documento.',
                    'message': msg_error,
                    'type': 'danger',
                    'sticky': True,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        except Exception as e:
            _logger.error('Error detectado al publicar el documento. Mensaje de ERROR: ' + tools.ustr(e))

            if move._context.get('massive', False):
                return False
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': f'Error al emitir el documento tributario.',
                        'message': e,
                        'type': 'danger',
                        'sticky': True,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
        else:
            _logger.info("Haz probado certificar FEL!")
            return certificate

    def button_cancel_with_reason(self):
        """Método ejecutado por la acción de un usuario final, útil para abrir un wizard,
         para el ingreso de la razón de cancelación del documento fiscal necesario para las anulaciones FEL.
         siempre y cuando los recibos estén confirmados y no hayan sido pagados.
         :return: action window para visualizar un wizard.
        """
        if self.dont_cancel_move:  # TODO: mejora.
            raise ValidationError(
                _("The accounting date being set prior to the %(lock_type)s lock date %(lock_date)s, "
                  "it will be changed to %(accounting_date)s upon posting.",
                  lock_type='',
                  lock_date=format_date(self.env, self.company_id.tax_lock_date),
                  accounting_date=format_date(self.env, self.company_id.tax_lock_date)
                  )
            )

        return {
            'name': "Ingrese la razón de la anulación del DTE",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'account.move.cancel_reason',
            'views': [[self.env.ref('l10n_gt_inteligos_fel.view_move_form_cancel').id, 'form']],
            'target': 'new',
            'context': dict(default_move_id=self.id)
        }

    def button_cancel(self):
        """"""
        for move in self:
            if move.journal_id.its_fel:
                if move.company_id.fel_provider == 'IN':
                    dte_fel_to_cancel = InfileFel.fel_dte()
                elif move.company_id.fel_provider == 'DI':
                    dte_fel_to_cancel = DigifactFel.fel_dte()
                elif move.company_id.fel_provider == 'MP':
                    dte_fel_to_cancel = MegaPrintFel.fel_dte()
                elif move.company_id.fel_provider == 'ECO':
                    dte_fel_to_cancel = EcofacturaFel.fel_dte()
                elif move.company_id.fel_provider == 'FC':
                    dte_fel_to_cancel = eForconFel.fel_dte()
                else:
                    raise ValidationError('No has seleccionado a ningún proveedor para la emisión FEL. '
                                          'Debe ser configurado en la compañía emisora. '
                                          'Por favor hazlo o comunícate con administración.')

                gt = timezone('America/Guatemala')
                utc_dt = datetime.now(tz=UTC).astimezone(gt)
                date_cancel = utc_dt.strftime("%Y-%m-%dT%H:%M:%S") + '-06:00'

                if not move.partner_id.vat:
                    raise ValidationError('El cliente no tiene NIT. Falta agregarlo.')

                fel_date = move.fel_date
                fel_uuid = move.fel_uuid

                if not fel_date or not fel_uuid:
                    raise ValidationError('No existe documento FEL para anular.')

                if move.company_id.fel_provider in ['IN', 'ECO']:
                    credentials = [move.company_id.fel_pass, move.company_id.fel_pass_sign,
                                   move.company_id.fel_user, move.company_id.vat, move.company_id.email]
                elif move.company_id.fel_provider in ['DI', 'MP']:
                    credentials = [move.company_id.token]
                elif move.company_id.fel_provider == "FC":
                    credentials = [move.fel_number, move.fel_serie, move.company_id.fel_user,
                                   move.company_id.fel_pass, move.company_id]
                else:
                    raise ValidationError('No ha seleccionado a ningún proveedor para la emisión FEL. '
                                          'Debe ser configurado en la compañía emisora. '
                                          'Por favor hágalo o comuníquese con administración.')

                for credential in credentials:
                    if not credential:
                        raise ValidationError('La compañía no está bien configurada. Hay campos sin datos.')

                # # identificador unico del dte del cliente
                identifier = move.name

                if not move.key_identifier:
                    identifier = move.set_key_identifier()
                    move.key_identifier = identifier
                elif move.key_identifier:
                    identifier = move.key_identifier
                dte_fel_to_cancel.set_clave_unica(identifier)
                cancel_fel = False
                reason_sanitized = move.examine_values(
                    {'reason': move.reason_note if isinstance(move.reason_note, str) else '**Cancelación**'},
                    'Anulación de documento')

                if move.company_id.fel_provider == 'IN':
                    cancel_fel = dte_fel_to_cancel.anular(date_cancel,
                                                          move.company_id.vat.replace("-", ""),
                                                          fel_date,
                                                          move.partner_id.vat.replace("-", ""), fel_uuid,
                                                          reason_sanitized.get('reason'),
                                                          move.company_id.fel_pass,
                                                          move.company_id.fel_pass_sign, move.company_id.fel_user,
                                                          move.company_id.vat, move.company_id.email,
                                                          move.company_id
                                                          )
                elif move.company_id.fel_provider == 'DI':
                    cancel_fel = dte_fel_to_cancel.anular(date_cancel,
                                                          move.company_id.vat.replace("-", ""),
                                                          fel_date,
                                                          move.partner_id.vat.replace("-", ""), fel_uuid,
                                                          reason_sanitized.get('reason'), move.company_id.token,
                                                          move.company_id.vat_digifact,
                                                          move.company_id
                                                          )
                elif move.company_id.fel_provider == 'MP':
                    cancel_fel = dte_fel_to_cancel.anular(date_cancel,
                                                          move.company_id.vat.replace("-", ""),
                                                          fel_date,
                                                          move.partner_id.vat.replace("-", ""), fel_uuid,
                                                          reason_sanitized.get('reason'), move.company_id.token,
                                                          move.company_id
                                                          )
                elif move.company_id.fel_provider == 'ECO':
                    cancel_fel = dte_fel_to_cancel.anular(fel_uuid, reason_sanitized.get('reason'),
                                                          move.company_id.fel_pass, move.company_id.fel_pass_sign,
                                                          move.company_id.fel_user,
                                                          move.company_id.vat.replace("-", ""), move.company_id)
                elif move.company_id.fel_provider == 'FC':
                    cancel_fel = dte_fel_to_cancel.anular(move.fel_number, move.fel_serie,
                                                          reason_sanitized.get('reason'),
                                                          move.company_id.fel_user, move.company_id.fel_pass,
                                                          move.company_id)

                canceled = move.response_dte_fel(cancel_fel, 'doc_xml_cancel_generated', 'certify_cancel_xml',
                                                 'signed_cancel_xml', 'fel_uuid_cancel', 'fel_date_cancel',
                                                 'fel_series_cancel', 'fel_number_cancel', move.id)

                if canceled:
                    super(AccountMoveInherited, move).button_cancel()
                    move.mapped('line_ids').remove_move_reconcile()
                    if move.company_id.fel_provider == 'MP':
                        """Obtiene el formato .pdf de la actual emisión de Megaprint"""
                        move.get_pdf()

                    if move.company_id.send_invoice_email_fel and move.state == 'cancel' \
                            and move.key_identifier:
                        move.action_send_by_mail_invoice_cancel_fel()
            else:
                super(AccountMoveInherited, move).button_cancel()
                move.mapped('line_ids').remove_move_reconcile()

    def action_post(self):
        """
        Herencia del método propio de Odoo para agregarle lógica para administrar las emisiones FEL.
        :return: respuesta genérica del método o notificación de error de base de datos por emisiones simultáneas.
        """
        if not self._context.get('massive', False):
            parallel_record_ams = self._check_parallel_diff_records()

            if parallel_record_ams:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': f'Error de base de datos, por favor no publique de nuevo el documento.',
                        'message': _(f'Modifications are being made to some documents simultaneously, please '
                                     f'waiting that will done and try again. Updated record:  '
                                     f'{", ".join([rec.name for rec in parallel_record_ams])}'),
                        'type': 'danger',
                        'sticky': True,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }

        for move in self.filtered(lambda m: m.state == 'draft'):
            # move.country_code == 'GT'
            if move.journal_id.its_fel and move.country_code == 'GT':
                certificate_dte_fel = move.dte_fel()

                if isinstance(certificate_dte_fel, bool) and certificate_dte_fel:

                    if move.company_id.fel_provider == "MP":
                        try:
                            """Obtiene el formato .pdf de la actual emisión de Megaprint"""
                            move.get_pdf()
                        except Exception as e:
                            error_msg = {'resultado': False,
                                         "descripcion_errores": [{
                                             "mensaje_error": tools.ustr(e), "fuente": '',
                                             "categoria": '', "numeral": '#', "validacion": ''
                                         }], 'archivo': 'Hubo un error en la comunicación.',
                                         'descripcion': tools.ustr(e)
                                         }
                            error_msg.update({"xml_plano": move.doc_xml_generated})
                            move.response_dte_fel(error_msg, 'doc_xml_generated', 'certify_xml',
                                                  'signed_xml', 'fel_uuid', 'fel_date',
                                                  'fel_serie', 'fel_number', move.id)

                    try:
                        super(AccountMoveInherited, move).action_post()
                        move.write({'process_fel': False})
                    except (InternalError, Error, DatabaseError, OperationalError) as d:
                        msg_error = f"ERROR Odoo con FEL: {d}"
                        _logger.error(msg_error)
                        move.write({'error_serialization': True})
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': f'Error de base de datos, por favor no publique de nuevo el documento.',
                                'message': msg_error,
                                'type': 'danger',
                                'sticky': True,
                                'next': {'type': 'ir.actions.act_window_close'},
                            }
                        }
                    except Exception as e:
                        _logger.error('Error detectado al publicar el documento. Mensaje de ERROR: ' + tools.ustr(e))
                    else:
                        if move.company_id.send_invoice_email_fel \
                                and move.fel_uuid and move.key_identifier:

                            move.action_send_by_mail_invoice_certificate()

                elif isinstance(certificate_dte_fel, dict):
                    return certificate_dte_fel
            else:
                super(AccountMoveInherited, move).action_post()
                move.write({'process_fel': False})
        return False

    def action_server_massive_post_fel(self):
        """
        Acción de servidor para la emisión masiva de DTEs.
        :return: None
        """
        for record in self.filtered(
                lambda move: move.move_type in ['out_invoice', 'out_refund'] and move.state == 'draft'):
            record.with_context(default_move_type=record.move_type, massive=True).action_post()

    def _get_sequence(self):
        """
        Sobreescritura de método _get_sequence para obtener
            la secuencia usada según el tipo de documento del doc a emitir con FEL.
        """
        self.ensure_one()
        journal = self.journal_id
        if self.move_type in ('entry', 'out_invoice', 'in_invoice', 'out_receipt', 'in_receipt') \
                or not journal.refund_sequence:
            return journal.sequence_id
        elif self.move_type == 'out_refund' and journal.refund_sequence:
            doc_type = self.invoice_doc_type.doc_code_prefix or ''
            if doc_type.strip() == 'NCRE':
                return journal.refund_sequence_id
            elif doc_type.strip() == 'NDEB':
                return journal.ndeb_sequence_id
            elif doc_type.strip() == 'NABN':
                return journal.nabn_sequence_id
        else:
            return journal.refund_sequence_id

    @api.constrains('invoice_doc_type')
    def check_invoice_doc_type(self):
        """Metodo para chequear el tipo de documento ingresado en las facturas de clientes."""
        if self.env.company.account_fiscal_country_id.code != 'CR':
            for record in self:
                document_type_ids = (record.env.ref('l10n_gt_td_generic.dc_fact').id,
                                     record.env.ref('l10n_gt_td_generic.dc_reci').id,
                                     record.env.ref('l10n_gt_td_generic.dc_fcam').id)

                if record.move_type == 'out_invoice' and record.invoice_doc_type.id not in document_type_ids:
                    raise ValidationError('Debe ingresar únicamente el tipo de documento: '
                                          'Factura, Factura Cambiaria o Recibo')

    def get_pdf(self):
        """Función útil únicamente para Megaprint.
            Obtiene el formato .pdf del UUID de la emisión indicada.
        """
        uuid = self.fel_uuid
        url = "https://apiv2.ifacere-fel.com/api/retornarPDF"
        xml = """<?xml version="1.0" encoding="UTF-8"?> 
                <RetornaPDFRequest> 
                <uuid>""" + uuid + """</uuid> 
                </RetornaPDFRequest>"""
        token = self.company_id.token
        headers = {
            'Authorization': "bearer " + token,
            'Content-Type': 'application/xml; charset=utf-8'
        }
        r = requests.post(url=url, data=xml.encode('utf-8'), headers=headers)
        pdf = False
        for item in r.text.split("</pdf>"):
            if "<pdf>" in item:
                pdf = item[item.find("<pdf>") + len("<pdf>"):]
        if pdf:
            self.env['ir.attachment'].create({
                'name': "Documento Emitido.pdf",
                'type': 'binary',
                'datas': pdf,
                'store_fname': "PDF",
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/x-pdf'
            })
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'No ha sido posible obtener el documento .pdf que Megaprint genera.',
                    'sticky': True,
                    'type': 'danger'
                }
            }

    def write(self, vals):
        """
        Herencia del método propio de Odoo para agregar lógica que permita obtener desde los documentos
        fiscales y contables el valor de los campos dirección de calle, dirección de calle 2,
        código postal, municipio, departamento, país, razón social y NIT del contacto seleccionado.
        :return: registro actualizado.
        """
        for record in self:
            if (record.state == 'draft' or vals.get('posted_before')) and record.partner_id:
                vals.update({'street': record.partner_id.street, 'street2': record.partner_id.street2,
                             'zip': record.partner_id.zip, 'email': record.partner_id.email,
                             'nit': record.partner_id.vat, 'legal_name': record.partner_id.legal_name,
                             'county_id': record.partner_id.county_id.id if record.partner_id.county_id else False,
                             'state_id': record.partner_id.state_id.id if record.partner_id.state_id else False,
                             'country_id': record.partner_id.country_id.id if record.partner_id.country_id else False})
        result = super(AccountMoveInherited, self).write(vals)
        return result

    def action_send_by_mail_invoice_certificate(self):
        """
        Método para enviar el correo electrónico de la emisión de la factura electrónica
        certificada.
        :return: None
        """
        for record in self:
            template = self.env.ref('l10n_gt_inteligos_fel.email_template_fel_send')
            template.send_mail(record.id, email_layout_xmlid='mail.mail_notification_light',
                               force_send=True)

    def action_send_by_mail_invoice_cancel_fel(self):
        """
        Método para enviar el correo electrónico de la emisión de la factura electrónica
        anulada con certificación (FEL).
        :return: None
        """
        for record in self:
            template = self.env.ref('l10n_gt_inteligos_fel.email_template_cancel_fel_send')
            template.send_mail(record.id, email_layout_xmlid='mail.mail_notification_light',
                               force_send=True)


    def _get_view(self, view_id=None, view_type='form', **options):
        """
        Método tentativo para ocultar columnas en vista tree
        """
        arch, view = super()._get_view(view_id, view_type, **options)
        
        country_code = self.env.company.account_fiscal_country_id.code
        _logger.info(f'country_code: {country_code}')

        if view_type == 'tree' and country_code != 'GT':
            for field_name in ['fel_serie', 'fel_number']:
                nodes = arch.xpath(f"//field[@name='{field_name}']")
                for node in nodes:
                    node.set('invisible', '1')
        
        return arch, view
