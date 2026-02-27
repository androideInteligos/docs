# -*- coding: utf-8 -*-

import requests
import logging
from xml.etree.ElementTree import fromstring, ElementTree
from . import eForconEmisor
from . import eForconReceptor
from odoo.tools import ustr

_logger = logging.getLogger(__name__)


class complemento_notas():
    def __init__(self):
        self.xml = ''
        self.lista_complementos = []

    def agregar(self, RegimenAntiguo, MotivoAjuste, FechaEmisionDocumentoOrigen, SerieDocumentoOrigen,
                NumeroAutorizacionDocumentoOrigen, NumeroDocumentoOrigen):
        self.lista_complementos.append({"RegimenAntiguo": RegimenAntiguo,
                                        "MotivoAjuste": MotivoAjuste,
                                        "FechaEmisionDocumentoOrigen": FechaEmisionDocumentoOrigen,
                                        "NumeroDocumentoOrigen": NumeroDocumentoOrigen,
                                        "SerieDocumentoOrigen": SerieDocumentoOrigen,
                                        "NumeroAutorizacionDocumentoOrigen": NumeroAutorizacionDocumentoOrigen
                                        })

    def to_xml(self):
        self.xml = ''

        for complemento in self.lista_complementos:
            if complemento["RegimenAntiguo"] == 'ANTIGUO':
                self.xml += '<tipoRegimenDTE>' + 'FACE' + '</tipoRegimenDTE>'
                self.xml += '<numeroAutorizacion>' + \
                            str(complemento["NumeroAutorizacionDocumentoOrigen"]) + '</numeroAutorizacion>'
                self.xml += '<motivoAjuste>' + str(complemento["MotivoAjuste"]) + '</motivoAjuste>'
                self.xml += '<fechaEmisionOrigen>' + \
                            str(complemento["FechaEmisionDocumentoOrigen"]) + '</fechaEmisionOrigen>'
                self.xml += '<numeroOrigenFace>' + str(complemento["NumeroDocumentoOrigen"]) + '</numeroOrigenFace>'
                self.xml += '<serieOrigenFace>' + str(complemento["SerieDocumentoOrigen"]) + '</serieOrigenFace>'
            else:
                self.xml += '<tipoRegimenDTE>' + 'FEL' + '</tipoRegimenDTE>'
                self.xml += '<numeroAutorizacion>' + \
                            str(complemento["NumeroAutorizacionDocumentoOrigen"]) + '</numeroAutorizacion>'
                self.xml += '<motivoAjuste>' + str(complemento["MotivoAjuste"]) + '</motivoAjuste>'
                self.xml += '<fechaEmisionOrigen>' + \
                            str(complemento["FechaEmisionDocumentoOrigen"]) + '</fechaEmisionOrigen>'
                self.xml += '<numeroOrigenFace>' + str(complemento["NumeroDocumentoOrigen"]) + '</numeroOrigenFace>'
                self.xml += '<serieOrigenFace>' + str(complemento["SerieDocumentoOrigen"]) + '</serieOrigenFace>'
        return self.xml


class complemento_exportacion():
    def __init__(self):
        self.xml = ''
        self.lista_complementos = []

    def agregar(self, NombreConsignatarioODestinatario, DireccionConsignatarioODestinatario,
                CodigoConsignatarioODestinatario, NombreComprador, DireccionComprador, CodigoComprador, OtraReferencia,
                INCOTERM, NombreExportador, CodigoExportador, LugarExpedicion, PaisConsignatario):
        # TODO SERÁN REMOVIDOS:
        # CodigoConsignatarioODestinatario
        # NombreComprador
        # DireccionComprador
        # CodigoComprador
        self.lista_complementos.append(
            {"NombreConsignatarioODestinatario": NombreConsignatarioODestinatario,
             "DireccionConsignatarioODestinatario": DireccionConsignatarioODestinatario,
             "CodigoConsignatarioODestinatario": CodigoConsignatarioODestinatario,
             "NombreComprador": NombreComprador,
             "DireccionComprador": DireccionComprador,
             "CodigoComprador": CodigoComprador,
             "OtraReferencia": OtraReferencia,
             "INCOTERM": INCOTERM,
             "NombreExportador": NombreExportador,
             "CodigoExportador": CodigoExportador,
             "LugarExpedicion": LugarExpedicion,
             "PaisConsignatario": PaisConsignatario
             }
        )

    def to_xml(self):
        self.xml = ''

        for complemento in self.lista_complementos:
            self.xml += '<LugarExpedicionEXP>' + str(complemento["LugarExpedicion"]) + '</LugarExpedicionEXP>'
            self.xml += '<nombreConsignatarioEXP>' + str(
                complemento["NombreConsignatarioODestinatario"]) + '</nombreConsignatarioEXP>'
            self.xml += '<direccionConsignatarioEXP>' + str(
                complemento["DireccionConsignatarioODestinatario"]) + '</direccionConsignatarioEXP>'
            self.xml += '<incotermEXP>' + str(complemento["INCOTERM"]) + '</incotermEXP>'
            self.xml += '<codigoConsignatarioEXP>' + str(
                complemento["CodigoConsignatarioODestinatario"]) + '</codigoConsignatarioEXP>'
            self.xml += '<nombreCompradorEXP>' + str(complemento["NombreComprador"]) + '</nombreCompradorEXP>'
            self.xml += '<direccionCompradorEXP>' + str(
                complemento["DireccionComprador"]) + '</direccionCompradorEXP>'
            self.xml += '<codigoCompradorEXP>' + str(complemento["CodigoComprador"]) + '</codigoCompradorEXP>'
            self.xml += '<PaisConsignatarioEXP>' + str(complemento["PaisConsignatario"]) + '</PaisConsignatarioEXP>'
            self.xml += '<otraReferenciaEXP>' + str(complemento["OtraReferencia"]) + '</otraReferenciaEXP>'
            self.xml += '<nombreExportadorEXP>' + str(complemento["NombreExportador"]) + '</nombreExportadorEXP>'
            self.xml += '<codigoExportadorEXP>' + str(complemento["CodigoExportador"]) + '</codigoExportadorEXP>'
        return self.xml


class complemento_especial():
    def __init__(self):
        self.xml = ''
        self.lista_complementos = []

    def agregar(self, retencion_isr, retencion_iva, total_menos_retenciones):
        self.lista_complementos.append({"RetencionISR": retencion_isr, "RetencionIVA": retencion_iva,
                                        "TotalMenosRetenciones": total_menos_retenciones})

    def to_xml(self):
        self.xml = ''

        for complemento in self.lista_complementos:
            self.xml += '<cfe:RetencionISR>' + str(complemento["RetencionISR"]) + '</cfe:RetencionISR>'
            self.xml += '<cfe:RetencionIVA>' + str(complemento["RetencionIVA"]) + '</cfe:RetencionIVA>'
            self.xml += '<cfe:TotalMenosRetenciones>' + str(
                complemento["TotalMenosRetenciones"]) + '</cfe:TotalMenosRetenciones>'
        return self.xml


class complemento_cambiaria():
    def __init__(self):
        self.xml = ''
        self.lista_complementos = []

    def to_xml(self):
        self.xml = ''

        for complemento in self.lista_complementos:
            self.xml += '<numeroAbonosCAMB>' + str(complemento["numero_abono"]) + '</numeroAbonosCAMB>'
            self.xml += '<fechaInicialVenceCAMB>' + str(
                complemento["fecha_vencimiento"]) + '</fechaInicialVenceCAMB>'
            self.xml += '<diasEntreAbonosCAMB>' + str(complemento["dias_abono"]) + '</diasEntreAbonosCAMB>'
        return self.xml

    def agregar(self, num_abono, fec_vencimiento, dias_abono):
        self.lista_complementos.append(
            {"numero_abono": num_abono, "fecha_vencimiento": fec_vencimiento, "dias_abono": dias_abono})


class adenda:
    def __init__(self):
        self.nombre = ''
        self.valor = ''

    def set_nombre(self, n):
        self.nombre = n

    def set_valor(self, v):
        self.valor = v

    def to_xml(self):
        return '<definicionEE><codigoEtiquetaEE>' + self.nombre + '</codigoEtiquetaEE><valorEtiquetaEE>' + self.valor + '</valorEtiquetaEE></definicionEE>'


class item:
    def __init__(self):
        self.numero_linea = 0
        self.bien_o_servicio = ''
        self.Cantidad = 0
        self.UnidadMedida = 'UND'
        self.Descripcion = ''
        self.PrecioUnitario = 0
        self.Descuento = 0
        self.TasaMunicipal = 0
        self.nombre_corto_impuesto = 'IVA (AFECTO)'
        self.xml_plano = ''

    def set_nombre_corto_impuesto(self, nombre_corto_impuesto):
        self.nombre_corto_impuesto = nombre_corto_impuesto

    def set_numero_linea(self, numero):
        self.numero_linea = numero

    def set_bien_o_servicio(self, bien_servicio):
        self.bien_o_servicio = bien_servicio

    def set_cantidad(self, cant):
        self.Cantidad = cant

    def set_unidad_medida(self, unit):
        self.UnidadMedida = unit

    def set_descripcion(self, desc):
        self.Descripcion = desc

    def set_precio_unitario(self, precio_unitario):
        self.PrecioUnitario = precio_unitario

    def set_descuento(self, descuento):
        self.Descuento = descuento

    def set_tasamunicipal(self, tasa):
        self.TasaMunicipal = tasa

    def to_xml(self):
        xml = ''
        xml += '<definicionDP><numeroItem>' + str(self.numero_linea) + '</numeroItem>'
        xml += '<bienServicio>' + str(self.bien_o_servicio) + '</bienServicio>'
        xml += '<nombreCortoImpuesto>' + self.nombre_corto_impuesto + '</nombreCortoImpuesto>'
        xml += '<cantidad>' + str(self.Cantidad) + '</cantidad>'
        xml += '<metrica>' + self.UnidadMedida + '</metrica>'
        xml += '<valorTasaMunicipal>' + str(self.TasaMunicipal) + '</valorTasaMunicipal>'
        xml += '<descripcion>' + self.Descripcion + '</descripcion>'
        xml += '<precioUnitario>' + str(self.PrecioUnitario) + '</precioUnitario>'
        xml += '<descuento>' + str(self.Descuento) + '</descuento>'
        xml += '</definicionDP>'
        return xml


class frase:
    def __init__(self):
        self.codigo = ''
        self.tipo = ''
        self.xml_plano = ''

    def to_xml(self):
        if self.xml_plano:
            return '<frases>' + self.xml_plano + '</frases>'
        else:
            return ""

    def set_frase(self, codigo_frase, tipo_frase):
        self.xml_plano += '<definicionFrase><codigoFrase>' + tipo_frase + '</codigoFrase>' + '<codigoEscenario>' + codigo_frase + '</codigoEscenario></definicionFrase>'


class fel_dte:
    def __init__(self):
        self.clave_unica = ''
        self.company = False
        self.emisor = eForconEmisor.emisor()
        self.receptor = eForconReceptor.receptor()
        self.frase_fel = frase()
        self.xml_plano = ''
        self.xml_certificado = ''
        self.datos_emisor = ''
        self.datos_generales = ''
        self.item_list = []
        self.lista_adendas = []
        self.lista_complementos = []
        self.GTDocumento = r'<?xml version="1.0" encoding="UTF-8" standalone="no"?><plantilla xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dte><encabezadoPrincipal>'
        self.exportacion = ''
        self.acceso = ''
        self.tipo_personeria = ''
        self.tipo_especial = ''
        self.codigo_moneda = ''
        self.fecha_hora_emision = ''
        self.tipo_dte = ''

    def anular(self, fel_number, fel_series, reason_cancel, user, key_certify, company):
        self.company = company
        self.xml_plano = """<web:AnularDteGenerico><web:sUsuario>""" + user + """</web:sUsuario><web:sClave>""" + key_certify + """</web:sClave><web:sNumeroDTE>""" + fel_number + """</web:sNumeroDTE><web:sSerieDTE>""" + fel_series + """</web:sSerieDTE><web:sMotivo>""" + reason_cancel + """</web:sMotivo></web:AnularDteGenerico>"""
        _logger.info('*********************')
        _logger.info(self.xml_plano)
        _logger.info('*********************')
        self.fel_certification = {}
        self.fel_certificacion_response = self.certificar_xml(self.xml_plano, "S")

        if self.fel_certificacion_response.get("resultado", False):
            self.fel_certification = {
                "resultado": True,
                "fecha": self.fel_certificacion_response["rwsFechaAnulacionDTE"],
                "uuid": '', "serie": '', "numero": '', "xml_plano": self.xml_plano,
                "xml_certificado": '', 'xml_firmado': self.fel_certificacion_response["signed_xml"]
            }
        else:
            self.fel_certification = self.fel_certificacion_response
            self.fel_certification["xml_plano"] = self.xml_plano
        return self.fel_certification

    def certificar(self, key_certify, user, company):
        self.company = company
        self.xml_plano += self.GTDocumento
        self.xml_plano += '<codigoInternoEmisor>' + self.clave_unica + '</codigoInternoEmisor>'
        self.xml_plano += self.emisor.to_xml()
        self.xml_plano += self.xml_datos_generales()
        self.xml_plano += self.receptor.to_xml()
        self.xml_plano += self.frase_fel.to_xml()
        self.xml_plano += self.xml_complementos()
        self.xml_plano += '</encabezadoPrincipal>'

        if self.item_list:
            self.xml_plano += '<detallePrincipal>'
            for item in self.item_list:
                self.xml_plano += item.to_xml()
            self.xml_plano += '</detallePrincipal>'

        if self.lista_adendas:
            self.xml_plano += '<encabezadoExtra>'
            for adenda in self.lista_adendas:
                self.xml_plano += adenda.to_xml()
            self.xml_plano += '</encabezadoExtra>'
        self.xml_plano += '</dte>'
        self.xml_plano += '</plantilla>'
        self.xml_plano = """<web:EmitirDteGenerico><web:sUsuario>""" + user + """</web:sUsuario><web:sClave>""" + key_certify + """</web:sClave><web:sXmlDte><![CDATA[""" + self.xml_plano + """]]></web:sXmlDte></web:EmitirDteGenerico>"""
        _logger.info('*********************')
        _logger.info(self.xml_plano)
        _logger.info('*********************')
        self.fel_certification = {}
        self.fel_certificacion_response = self.certificar_xml(self.xml_plano, "N")

        if self.fel_certificacion_response.get("resultado", False):
            self.fel_certification = {"resultado": True,
                                      "fecha": self.fel_certificacion_response["rwsFechaCertificaDTE"],
                                      "uuid": self.fel_certificacion_response["rwsAutorizacionUUID"],
                                      "serie": self.fel_certificacion_response["rwsSerieDTE"],
                                      "numero": self.fel_certificacion_response["rwsNumeroDTE"],
                                      "xml_plano": self.xml_plano,
                                      'xml_firmado': self.fel_certificacion_response["signed_xml"],
                                      "xml_certificado": self.fel_certificacion_response["rwsXMLCertificado"],
                                      "ruta_PDF": self.fel_certificacion_response["rwsRutaPDF"]
                                      }
        else:
            self.fel_certification = self.fel_certificacion_response
            self.fel_certification.update({"xml_plano": self.xml_plano})

        return self.fel_certification

    def agregar_complemento(self, complemento):
        self.lista_complementos.append(complemento)

    def set_tipo_especial(self, tipo_esp):
        self.receptor.set_especial(tipo_esp)

    def set_exportacion(self, exp):
        self.exportacion = exp

    def set_acceso(self, acceso):
        self.acceso = acceso

    def set_tipo_personeria(self, tipo_personeria):
        self.tipo_personeria = tipo_personeria

    def set_clave_unica(self, clave):
        self.clave_unica = clave

    def xml_complementos(self):
        xml_complemento = ''

        if self.lista_complementos:
            xml_complemento += '<complementos>'
            for complemento in self.lista_complementos:
                xml_complemento += complemento.to_xml()
            xml_complemento += '</complementos>'
        return xml_complemento

    def generar_expo(self):
        retorno = '<usoComercialDTE>LOCAL</usoComercialDTE>'

        if self.exportacion:
            retorno = '<usoComercialDTE>EXPORTACION</usoComercialDTE>'
        return retorno

    def generar_acceso(self):
        retorno = ' NumeroAcceso="' + self.acceso + '"' if self.acceso else ''
        return retorno

    def generar_tipo_personeria(self):
        retorno = ''
        if self.tipo_personeria:
            retorno = ' TipoPersoneria="' + self.tipo_personeria + '"'
        return retorno

    def set_datos_generales(self, codigo_moneda, fecha_hora_emision, tipo_dte):
        self.codigo_moneda = codigo_moneda
        self.fecha_hora_emision = fecha_hora_emision
        self.tipo_dte = tipo_dte

    def xml_datos_generales(self):
        self.datos_generales = self.generar_expo()
        # < numeroAccesoContingencia > """ + self.fecha_hora_emision + """"</numeroAccesoContingencia>
        self.datos_generales += """<tipoDTE>""" + self.tipo_dte + """</tipoDTE><fechaEmision>""" + self.fecha_hora_emision + """</fechaEmision><moneda>""" + self.codigo_moneda + """</moneda>"""
        return self.datos_generales

    def set_datos_emisor(self, emi):
        self.emisor = emi

    def set_datos_receptor(self, rec):
        self.receptor = rec

    def agregar_adenda(self, fel_adenda):
        self.lista_adendas.append(fel_adenda)

    def agregar_item(self, fel_item):
        self.item_list.append(fel_item)

    def access_number(self):
        counter_access_number = self.company.counter_access_number

        if counter_access_number <= 9999999:
            access_number = counter_access_number + 1
            self.company.counter_access_number += 1
            return access_number
        else:
            access_number = 1000000
            self.company.counter_access_number = 1
            return access_number

    def _parser_response(self, response, method):
        """Seccion para parsear xml firmado devuelto, para obtener los datos necesarios."""
        tree = ElementTree(fromstring(response))
        root = tree.getroot()

        list_nodes = root.getiterator()

        data = {}
        for node in list_nodes:
            if node.tag == '{http://www.eforcon.com/webservice}' + method + 'DteGenericoResponse':
                for element in node:
                    if element.tag == '{http://www.eforcon.com/webservice}' + method + 'DteGenericoResult':
                        for item_result in element:
                            data.update({item_result.tag.split('}')[1]: item_result.text})
        return data

    def certificar_xml(self, xml_plano, cancel):
        if cancel != "S":
            # UrlFirma = 'https://certificador.feel.com.gt/fel/certificacion/v2/dte'
            # url_cert = 'https://certificador.feel-rarp.com/fel/certificacion/v2/dte'
            method = 'Emitir'
            url_cert = self.company.get_url('certify')
        else:
            # UrlFirma = 'http://pruebasfel.eforcon.com/feldev/WSForconFel.asmx'
            # url_cert = 'https://certificador.feel-rarp.com/fel/anulacion/v2/dte'
            method = 'Anular'
            url_cert = self.company.get_url('cancel')
        data = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:web="http://www.eforcon.com/webservice"><soapenv:Header/><soapenv:Body>"""
        data += xml_plano + """</soapenv:Body></soapenv:Envelope>"""
        headers = {'Content-Type': 'text/xml'}

        try:
            response = requests.post(url=url_cert, data=data, headers=headers)
            fel_cert_response = {'resultado': True}
        except requests.exceptions.Timeout as timeout:
            access_number = self.access_number()
            fel_cert_response = {
                'resultado': False,
                "descripcion_errores": [{
                    "mensaje_error": ustr(timeout), "fuente": '',
                    "categoria": 'ERROR DE COMUNICACIÓN POR TIEMPO DE ESPERA EXCEDIDO', "numeral": '#', "validacion": ''
                }], 'archivo': 'Hubo un error (excepción) en la comunicación.',
                'descripcion': ustr(timeout), 'access_number': access_number
            }
        except Exception as e:
            _logger.error('Error al realizar el consumo del servicio para certificar de documento FEL, '
                          'respuesta de error obtenida: ' + ustr(e))
            fel_cert_response = {
                'resultado': False,
                "descripcion_errores": [{
                    "mensaje_error": ustr(e), "fuente": '',
                    "categoria": 'ERROR DE COMUNICACIÓN GENERAL', "numeral": '#', "validacion": ''
                }], 'archivo': 'Hubo un error (excepción) en la comunicación.',
                'descripcion': ustr(e)
            }
        else:
            try:
                if response.status_code in [522, 524]:
                    access_number = self.access_number()
                    fel_cert_response.update({'access_number': access_number})

                parser_response = self._parser_response(response.text, method)

                if parser_response.get('rwsResultado', '') == 'false':
                    errors = []
                    for error in parser_response.get('rwsDescripcion', ' ').strip().split("ERROR"):
                        if error:  # Esta validación la hago pues eForcon devuelve un str de errores con espacios en blanco.
                            errors.append({
                                "mensaje_error": error, "fuente": '',
                                "categoria": '', "numeral": '', "validacion": error.split(':')[0]
                            })
                    fel_cert_response.update({
                        'resultado': False, 'signed_xml': data,
                        "descripcion_errores": errors, 'archivo': 'Hubo un error en los datos enviados.',
                        'descripcion': "Existen errores en la validacion del XML. Por favor revisa e intenta de nuevo."
                    })
                elif parser_response.get('rwsResultado', '') == 'true':
                    parser_response.update({'signed_xml': data})
                    fel_cert_response.update(parser_response)
                else:
                    fel_cert_response.update({
                        'resultado': False,
                        "descripcion_errores": [{
                                "mensaje_error": 'Comunicación http exitosa, pero no válida.', "fuente": 'eForcon',
                                "categoria": 'Error Externo', "numeral": '',
                                "validacion": 'Valor rwsResultado no existe en respuesta'
                            }], 'archivo': 'Hubo un error en los datos enviados.',
                        'descripcion': "Un error se ha dado del lado eForcon, consultar para mayor información. "
                                       "Respuesta: " + response.text
                    })
            except Exception as e:
                fel_cert_response.update({
                    'resultado': False,
                    "descripcion_errores": [{
                        "mensaje_error": ustr(e), "fuente": 'Odoo',
                        "categoria": 'Error Interno', "numeral": '', "validacion": ''
                    }], 'archivo': 'Hubo un error al preparar los datos de respuesta.',
                    'descripcion': "Un error se ha dado del lado de Odoo, consultar para mayor información. "
                                   "Respuesta: " + response.text
                })
        return fel_cert_response
