# -*- coding: utf-8 -*-

import requests
import json
from zeep import Client
from xml.etree.ElementTree import fromstring, ElementTree

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource


class ResCompanyInherit(models.Model):
    _inherit = "res.company"
    _name = "res.company"

    fel_provider = fields.Selection(
        selection=[
            ('IN', "INFILE"), ('DI', "DIGIFACT"), ('CO', "CONTAP"), ('FC', 'eFORCON'),
            ('MP', "MEGAPRINT"), ('ECO', "ECOFACTURAS")
        ], default=False, string="Proveedor"
    )
    fel_iva = fields.Selection(
        selection=[
            ('GEN', "General"),
            ('EXE', "Exento"),
            ('PEQ', "Pequeño Contribuyente")
        ], default=False, string="Tipo-Contribuyente"
    )
    its_fel = fields.Boolean(string="Tiene Factura Electrónica", default=False)
    fel_user = fields.Char(string="Usuario")
    fel_pass_sign = fields.Char(string="Llave de Firma")
    fel_pass = fields.Char(string="Llave de Certificación")
    establishment_number = fields.Char(string="No. Establecimiento")
    fel_phrases_ids = fields.Many2many('account.fel_phrases', 'res_company_fel_phrase_rel', 'company_id',
                                       'fel_phrase_id', string='Frases FEL')
    legal_name = fields.Char(string='Razón Social', help="Este campo será tomado como la razón social de la compañía, "
                                                         "información enviada a FEL como Nombre en los documentos "
                                                         "eletrónicos del emisor.")
    exporter_code = fields.Char(string='Código de Exportación',
                                help="Este campo será tomado como el código de exportación de la compañía, "
                                     "información enviada a FEL para los documentos "
                                     "eletrónicos de exportación.")
    adendas_ids = fields.One2many(
        "company.adendas_fel",
        "company_id",
        string='Adendas FEL',
        help="Estos registros son las adendas que usará el emisor por tipo de documento."
    )
    vat_digifact = fields.Char(
        string='Código de acceso (NIT)',
        help="Este campo será tomado como el código de acceso para obtener "
             "el token correspondiente de la compañía, "
             "información enviada a FEL para la emisión de los documentos "
             "eletrónicos con DIGIFACT."
    )
    password = fields.Char(
        string='Contraseña',
        help="Este campo será tomado como la cotraseña correspondiente de la compañía, "
             "información enviada a FEL para la emisión de los documentos "
             "eletrónicos con DIGIFACT."
    )
    token = fields.Char(
        readonly=True,
        string='Token',
        help="Este campo será tomado como el token correspondiente de la compañía, "
             "información enviada a FEL para la emisión de los documentos "
             "eletrónicos con DIGIFACT. "
    )
    date_due = fields.Char(
        readonly=True,
        string='Expiración Token',
        help="Esta es la fecha de expiración del token correspondiente de la compañía, "
             "información que deberá ser actualizada cada año para la emisión de los documentos "
             "eletrónicos con DIGIFACT."
    )
    counter_access_number = fields.Integer(
        default=1000000,
        string='Contador número de acceso.',
        help="Este campo es útil para llevar la cuantificacion de contigencias que se hayan dado."
    )
    """Actualización del 28.06.2021
        mejora para agregar campo boleano para configuración del ingreso de direcciones FEL.
    """
    mandatory_address_fel = fields.Boolean(
        store=True,
        index=True,
        string="¿Ingresar direcciones FEL?",
    )
    """Fin actualización del 28.06.2021
        mejora para agregar campo boleano para configuración del ingreso de direcciones FEL.
    """
    """Actualización del 13.09.2021
        mejora para configurar por compañía las urls para emisiones FEL según el ambiente que se esté.
    """
    env_fel = fields.Selection(
        selection=[
            ('test', 'Pruebas'),
            ('production', 'Producción')
        ],
        required=True, default='test',
        string='Entorno de emisión',
        help="El uso de las emisiones se dan en dos entornos: Pruebas, "
             "para evaluar que la integración con el certificador es correcta "
             "y Producción, para utilizarlo en el diario vivir de las emisiones."
    )
    fel_url_ids = fields.One2many(
        comodel_name="company.fel_url",
        inverse_name="company_id",
        string='Urls de Fel',
        help="Estos registros son las urls que se usarán para las "
             "certificaciones el emisor según el ambiente en el que esté."
    )
    doc_identifier = fields.Integer(
        default=1,
        string='Número de identificador.',
        help="Este campo es útil para llevar el contador de los números "
             "de identificadores dados para los documentos Ecofacturas."
    )
    amount_restrict_cf = fields.Float(default=2500.00, string='Monto restrictivo',
                                      help="Este campo es útil para almacenar el monto restrictivo "
                                           "para emisiones FEL con identificación de cliente CF")
    send_invoice_email_fel = fields.Boolean(
        string='Enviar correo electrónico con factura certificada',
        help="Este campo es útil para enviar el correo electrónico con la factura "
             "certificada de manera electrónica al cliente al momento de confirmar "
             "y certificar el DTE."
    )
    show_head_info_report_invoice = fields.Boolean(
        string='Mostrar información de factura en reporte',
        help="Este campo es útil para mostrar información de la factura en el encabezado "
             "del reporte genérico de Facturas."
    )
    nit_fel_provider = fields.Char(
        string='NIT del proveedor FEL',
        help="Este campo es útil para almacenar el NIT del proveedor FEL "
             "para mostrar en el reporte genérico."
    )

    def get_url(self, use_type):
        pair_urls = self.fel_url_ids.filtered(lambda url: url.use_type == use_type)
        if len(pair_urls) > 1:
            raise ValidationError('Hay más de un par de urls para el mismo tipo de operación deseada. '
                                  'Comuníquese con su administrador de sistema.')
        elif not pair_urls:
            raise ValidationError('No hay un par de urls para el tipo de operación deseada. '
                                  'Comuníquese con su administrador de sistema.')
        else:
            if self.env_fel == 'production':
                return pair_urls.prod_url
            elif self.env_fel == 'test':
                return pair_urls.test_url
            else:
                raise ValidationError('No hay una configuración apropiada para el entorno de emisión de la compañía. '
                                      'Comuníquese con su administrador de sistema.')

    """Fin actualización del 13.09.2021
        mejora para configurar por compañía las urls para emisiones FEL según el ambiente que se esté.
    """

    @api.model
    def _parser_request_xlm(self, response):
        """Parseo de xml de consulta.
            payload es el xml de la consulta en formato string. resp.text"""
        tree = ElementTree(fromstring(response))
        root = tree.getroot()
        datadict = {element.tag: element.text for element in root}
        return datadict

    def get_doc_identifier(self, dte_doc_type):
        xml_request = f"""<?xml version="1.0" encoding="UTF-8"?><Correlativo><NitEmisor>{self.vat.replace("-", "")}</NitEmisor><Establecimiento>{self.establishment_number}</Establecimiento><TipoDocumento>{dte_doc_type}</TipoDocumento></Correlativo>"""

        try:
            url_unique_number = self.get_url('unique_number')
            client = Client(url_unique_number)
            response = client.service.Execute(Cliente=self.fel_pass_sign, Usuario=self.fel_user,
                                              Clave=self.fel_pass, Consulta=xml_request)
            result = self._parser_request_xlm(response)
            error = result.get("Error")

            if error:
                raise ValidationError(error)
            doc_identifier = result.get("UltimaTransaccion")
            self.write({'doc_identifier': doc_identifier})
        except Exception as e:
            raise ValidationError(f'Se ha intentado obtener el correlativo de emisión registrado, '
                                  f'pero se obtuvo un error en el proceso de consulta '
                                  f'con el servicio Ecofacturas, ERROR: {e}. '
                                  f'Consultar con administración para más información.')
        else:

            if self.doc_identifier < 9999999999:
                self.doc_identifier += 1
                return str(self.doc_identifier)
            else:
                raise ValidationError('Ya se han completado el total de emisiones permitidas por Ecofacturas. '
                                      'Comuniquese con Ecofacturas para poder resolver esto, '
                                      'ya que es vital en las emisiones al no permitir documentos duplicados.')

    def get_token(self):
        """ Método útil para consultar, obtener y almacenar el token según cada proveedor FEL que aplique al cliente.
            Actualización del 25.10.2021
                Reformulación para obtener la url para obtener el token según el entorno en el que se encuentre el cliente.
                Mejora: url_token = self.get_url('token')
                Y reformular peticiones http para que dinámicamente consulte la url pasada.
                Ejemplo --->   r = requests.get(url_token, auth=(self.fel_user, self.password))
        """
        url_token = self.get_url('token')
        if self.fel_provider == "CO":
            # 'https://pruebas-contap-279823.appspot.com/generateToken'
            r = requests.get(url_token, auth=(self.fel_user, self.password))
            token = r.content

            if token:
                self.token = token
            else:
                raise ValidationError(token)
        elif self.fel_provider == "MP":
            xml = """<?xml version="1.0" encoding="UTF-8"?>
            <SolicitaTokenRequest>
            <usuario>""" + self.fel_user + """</usuario>
            <apikey>""" + self.password + """</apikey>
            </SolicitaTokenRequest>"""
            # 'https://apiv2.ifacere-fel.com/api/solicitarToken'
            r = requests.post(url_token, data=xml)
            response = r.content

            if r.status_code == 200:
                token = self._parser_request_xlm(response).get("token")
                self.token = token
        else:
            headers = {'content-type': 'application/json'}
            # url_token = 'https://felgttestaws.digifact.com.gt/felapiv2/api/login/get_token'

            if not self.vat_digifact or len(self.vat_digifact) != 12:
                raise ValidationError('El Número de acceso de la compañía emisora no tiene el formato debido, '
                                      'debe de tener 12 caracteres numéricos. '
                                      'Por favor verifique o comuníquese con Digifact.')
            if not self.fel_user:
                raise ValidationError('No ha ingresado el usuario DIGIFACT para la compañía emisora. '
                                      'Por favor hágalo y vuelva a intentar generar el token.')
            if not self.password:
                raise ValidationError('No ha ingresado la contraseña DIGIFACT para la compañía emisora. '
                                      'Por favor hágalo y vuelva a intentar generar el token.')
            if not self.country_id:
                raise ValidationError('No ha ingresado país para la compañía emisora. '
                                      'Por favor hágalo y vuelva a intentar generar el token.')
            country_code = self.country_id.code
            credentials = {
                "Username": country_code + '.' + self.vat_digifact + '.' + self.fel_user,
                "Password": self.password
            }

            cert_file_path = get_module_resource('l10n_gt_inteligos_fel', 'static/src/certs/', 'cert.pem')

            try:
                r = requests.post(
                    url=url_token, data=json.dumps(credentials),
                    headers=headers,
                    verify=cert_file_path,
                    timeout=10
                )
            except requests.RequestException as e:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error en la comunicación para obtener el "token"',
                        'message': e,
                        'type': 'danger',
                        'sticky': True,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }

            try:
                response = r.json()
            except requests.JSONDecodeError as e:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Error al extraer el objeto "json"',
                        'message': f', Respuesta: {r}, Error: {e}',
                        'type': 'danger',
                        'sticky': True,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
            else:
                token = response.get('Token', False)

                if token:
                    self.token = token
                    self.date_due = response["expira_en"]
                else:
                    raise ValidationError(response)


class FELAdendas(models.Model):
    _name = 'company.adendas_fel'
    _description = 'Adendas FEL'

    company_id = fields.Many2one('res.company', string='Compañía')
    doc_type_id = fields.Many2one(
        'l10n_latam.document.type',
        help="El tipo de documento seleccionado será para el cual la adenda se enviará únicamente. "
             "En caso de dejar vacío, se enviará para todo tipo de documento.",
        string='Tipo de Documento'
    )
    name = fields.Char(
        string='Nombre de Adenda', required=True,
        help="El nombre de la adenda debe ser con un formato sin espacios, por ejemplo: el_nombre."
    )
    model_id = fields.Selection(
        selection=[
            ('account.move', 'Factura'),
            ('res.partner', 'Contacto'),
            ('res.users', 'Usuario'),
            ('sale.order', 'Pedido de Venta'),
            ('res.company', 'Compañía'),
            ('account.payment.term', 'Plazos de pago'),
            ('product.template', 'Producto'),
        ],
        required=True,
        string='Modelo', help="El modelo seleccionado será para el cual se listará el posible campo a seleccionar."
    )
    field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        required=True,
        ondelete="cascade",
        string='Campo'
    )


class FELPhrases(models.Model):
    _name = 'account.fel_phrases'
    _description = 'Frases FEL'

    type = fields.Selection(
        [
            ('1', "(1) Frase de Retencion ISR"),
            ('2', "(2) Frase de Retencion IVA"),
            ('3', "(3) Frase no Genera Credito Fiscal"),
            ('4', "(4) Frase de Exento / No Afecto IVA"),
            ('5', "(5) Frases de facturas especiales"),
            ('6', "(6) Frases de contribuyente agropecuario"),
            ('7', "(7) Frases de regímenes electrónicos"),
            ('8', "(8) Frase de Exento de ISR"),
            ('9', "(9) Frases especiales")
        ], required=True
    )
    phrase = fields.Integer("Frase", required=True)
    name = fields.Char("Descripcion", required=True)
    company_ids = fields.Many2many('res.company', 'res_company_fel_phrase_rel',
                                   'fel_phrase_id', 'company_id', string='Company Phrases')
    fiscal_position_ids = fields.Many2many('account.fiscal.position', 'account_fiscal_position_fel_phrase_rel',
                                           'fel_phrase_id', 'fiscal_position_id', string='Fiscal Position Phrases')
    partner_ids = fields.Many2many('res.partner', 'res_partner_fel_phrase_rel',
                                   'fel_phrase_id', 'partner_id', string='Partner Phrases')
    journal_ids = fields.Many2many('account.journal', 'account_journal_fel_phrase_rel',
                                   'fel_phrase_id', 'journal_id', string='Journal Establishment Phrases')

    """Adición de campos de resolución en frases necesarios en algunos casos"""
    resolution_number = fields.Char(string="Número de Resolución")
    resolution_date = fields.Char(string="Fecha de Resolución")

class FiscalPositionInherit(models.Model):
    _inherit = "account.fiscal.position"
    _name = "account.fiscal.position"

    fel_phrases_ids = fields.Many2many('account.fel_phrases', 'account_fiscal_position_fel_phrase_rel',
                                       'fiscal_position_id', 'fel_phrase_id',
                                       string='Frases FEL')


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"
    _name = "res.partner"

    fel_phrases_ids = fields.Many2many('account.fel_phrases', 'res_partner_fel_phrase_rel', 'partner_id',
                                       'fel_phrase_id',
                                       string='Frases FEL')
    """Actualización 22/04/2021
                Mejora para envío de datos si el cliente es un consumidor final."""
    its_final_consumer = fields.Boolean(default=False, copy=False, string='Consumidor Final')
    """----------Fin de actualización 22/04/2021-------------"""

    """Actualización 27/04/2021 
        Mejora para cambiar el NIT a 'CF' si el cliente es un consumidor final."""

    @api.onchange('its_final_consumer')
    def onchange_its_final_consumer(self):
        if self.its_final_consumer:
            self.vat = 'CF'

    """----------Fin de actualización 27/04/2021-------------"""

    """Actualizacion 28/09/2022 Incluir varios correos para copiar la factura
    """
    invoice_email = fields.Char(string='Lista de correos electrónicos para envío de factura electrónica')
    """----Fin actualizacion 28/09/2022"""


class AccountJournalInherited(models.Model):
    _inherit = "account.journal"
    _name = "account.journal"

    """Actualizacion del 10/05/2021
        Mejoras para agregar nuevas secuencias para diarios. Seran las secuencias de notas de debito y de abono.
    """

    @api.depends('ndeb_sequence_id.use_date_range', 'ndeb_sequence_id.number_next_actual')
    def _compute_ndeb_seq_number_next(self):
        """Computación para 'ndeb_sequence_number_next' de acuerdo con la secuencia utilizada actualmente.
            Establecido el uso unicamente para diarios de clientes (ventas).
        """
        for journal in self:
            if not journal.refund_sequence or journal.type == 'purchase':
                journal.ndeb_sequence_number_next = 1
            elif journal.refund_sequence and not journal.ndeb_sequence_id:
                journal_vals = {
                    'name': journal.name,
                    'company_id': journal.company_id.id,
                    'code': journal.code,
                    'id': journal.id,
                    'doc_type_id': self.env.ref('l10n_gt_td_generic.dc_ndeb').id
                }
                journal.ndeb_sequence_id = self.sudo()._create_sequence(journal_vals, refund=True).id
                sequence = journal.ndeb_sequence_id._get_current_sequence()
                journal.ndeb_sequence_number_next = sequence.number_next_actual
            else:
                sequence = journal.ndeb_sequence_id._get_current_sequence()
                journal.ndeb_sequence_number_next = sequence.number_next_actual

    def _inverse_ndeb_seq_number_next(self):
        """Inverso para 'ndeb_sequence_number_next' que edita el siguiente número de la secuencia."""
        for journal in self:
            if journal.ndeb_sequence_id and journal.refund_sequence and journal.ndeb_sequence_number_next:
                sequence = journal.ndeb_sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.ndeb_sequence_number_next

    @api.depends('nabn_sequence_id.use_date_range', 'nabn_sequence_id.number_next_actual')
    def _compute_nabn_seq_number_next(self):
        """Computación para 'nabn_sequence_number_next' de acuerdo con la secuencia utilizada actualmente.
            Establecido el uso unicamente para diarios de clientes (ventas).
        """
        for journal in self:
            if not journal.refund_sequence or journal.type == 'purchase':
                journal.nabn_sequence_number_next = 1
            elif journal.refund_sequence and not journal.nabn_sequence_id:
                journal_vals = {
                    'name': journal.name,
                    'company_id': journal.company_id.id,
                    'code': journal.code,
                    'id': journal.id,
                    'doc_type_id': self.env.ref('l10n_gt_td_generic.dc_nabn').id
                }
                journal.nabn_sequence_id = self.sudo()._create_sequence(journal_vals, refund=True).id
                sequence = journal.nabn_sequence_id._get_current_sequence()
                journal.nabn_sequence_number_next = sequence.number_next_actual
            else:
                sequence = journal.nabn_sequence_id._get_current_sequence()
                journal.nabn_sequence_number_next = sequence.number_next_actual

    def _inverse_nabn_seq_number_next(self):
        """Inverso para 'nabn_sequence_number_next' que edita el siguiente número de la secuencia."""
        for journal in self:
            if journal.nabn_sequence_id and journal.refund_sequence and journal.nabn_sequence_number_next:
                sequence = journal.nabn_sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.nabn_sequence_number_next

    ndeb_sequence_id = fields.Many2one(
        comodel_name='ir.sequence', string='Secuencia Notas de Débito',
        help="Este campo contiene información relacionada a la numeración de notas de débito de este diario.",
        copy=False
    )
    ndeb_sequence_number_next = fields.Integer(
        string='Siguiente # para Notas de Débito',
        help='El siguiente número de secuencia será usado para la siguiente nota de débito.',
        compute='_compute_ndeb_seq_number_next',
        inverse='_inverse_ndeb_seq_number_next'
    )
    nabn_sequence_id = fields.Many2one(
        comodel_name='ir.sequence', string='Secuencia Notas de Abono',
        help="Este campo contiene información relacionada a la numeración de notas de abono de este diario.",
        copy=False
    )
    nabn_sequence_number_next = fields.Integer(
        string='Siguiente # para Notas de Abono',
        help='El siguiente número de secuencia será usado para la siguiente nota de abono.',
        compute='_compute_nabn_seq_number_next',
        inverse='_inverse_nabn_seq_number_next'
    )
