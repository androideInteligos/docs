from logging import getLogger
from zeep import Client
from zeep.exceptions import TransportError, IncompleteOperation
from xml.etree.ElementTree import fromstring, ElementTree
from . import EcofacturaEmisor
from . import EcofacturaReceptor
from odoo.tools import ustr

_logger = getLogger(__name__)


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
        if len(self.lista_complementos) > 0:
            self.xml += '<stdTWSNota>'

            for complemento in self.lista_complementos:
                self.xml += '<stdTWS.stdTWSNota.stdTWSNotaIt>'
                regime = '1' if complemento["RegimenAntiguo"] == 'ANTIGUO' else '0'
                self.xml += '<TDFEPRegimenAntiguo>' + regime + '</TDFEPRegimenAntiguo>'
                self.xml += '<TDFEPAutorizacion>' + str(
                    complemento["NumeroAutorizacionDocumentoOrigen"]) + '</TDFEPAutorizacion>'
                self.xml += '<TDFEPSerie>' + str(
                    complemento["SerieDocumentoOrigen"]) + '</TDFEPSerie>'
                self.xml += '<TDFEPNumero>' + str(
                    complemento["NumeroDocumentoOrigen"]) + '</TDFEPNumero>'
                self.xml += '<TDFEPFecEmision>' + str(
                    complemento["FechaEmisionDocumentoOrigen"]) + '</TDFEPFecEmision>'
                self.xml += '</stdTWS.stdTWSNota.stdTWSNotaIt>'
            self.xml += '</stdTWSNota>'
        return self.xml


class complemento_exportacion():
    def __init__(self):
        self.xml = ''
        self.lista_complementos = []

    def agregar(self, NombreConsignatarioODestinatario, DireccionConsignatarioODestinatario,
                CodigoConsignatarioODestinatario, NombreComprador, DireccionComprador, CodigoComprador, OtraReferencia,
                INCOTERM, NombreExportador, CodigoExportador, LugarExpedicion, PaisConsignatario):
        self.lista_complementos.append({
            "NombreConsignatarioODestinatario": NombreConsignatarioODestinatario,
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
        })

    def to_xml(self):
        self.xml = ''
        if len(self.lista_complementos) > 0:
            self.xml += '<stdTWSExp>'

            for complemento in self.lista_complementos:
                self.xml += '<stdTWS.stdTWSExp.stdTWSExpIt>'
                self.xml += '<NomConsigODest>' + str(
                    complemento["NombreConsignatarioODestinatario"]) + '</NomConsigODest>'
                self.xml += '<DirConsigODest>' + str(
                    complemento["DireccionConsignatarioODestinatario"]) + '</DirConsigODest>'
                self.xml += '<CodConsigODest>' + str(
                    complemento["CodigoConsignatarioODestinatario"]) + '</CodConsigODest>'
                self.xml += '<OtraRef>' + str(complemento["OtraReferencia"]) + '</OtraRef>'
                self.xml += '<INCOTERM>' + str(complemento["INCOTERM"]) + '</INCOTERM>'
                self.xml += '<ExpNom>' + str(complemento["NombreExportador"]) + '</ExpNom>'
                self.xml += '<ExpCod>' + str(complemento["CodigoExportador"]) + '</ExpCod>'
                self.xml += '<LugarExpedicion>' + str(complemento["LugarExpedicion"]) + '</LugarExpedicion>'
                self.xml += '<PaisConsigODest>' + str(complemento["PaisConsignatario"]) + '</PaisConsigODest>'
                self.xml += '</stdTWS.stdTWSExp.stdTWSExpIt>'
            self.xml += '</stdTWSExp>'

        return self.xml


class complemento_cambiaria():
    def __init__(self):
        self.xml = ''
        self.lista_complementos = []

    def agregar(self, num_abono, fec_vencimiento, mon_abono):
        self.lista_complementos.append({"numero_abono": num_abono, "fecha_vencimiento": fec_vencimiento,
                                        "monto_abono": mon_abono})

    def to_xml(self):
        self.xml = ''
        if self.lista_complementos:
            self.xml += '<stdTWSCam>'

            for complemento in self.lista_complementos:
                self.xml += '<stdTWS.stdTWSCam.stdTWSCamIt>'
                self.xml += '<TrnAbonoNum>' + str(complemento["numero_abono"]) + '</TrnAbonoNum>'
                self.xml += '<TrnAbonoFecVen>' + str(complemento["fecha_vencimiento"]) + '</TrnAbonoFecVen>'
                self.xml += '<TrnAbonoMonto>' + str(complemento["monto_abono"]) + '</TrnAbonoMonto>'
                self.xml += '</stdTWS.stdTWSCam.stdTWSCamIt>'
            self.xml += '</stdTWSCam>'
        return self.xml


class adenda:
    def __init__(self):
        self.name = ''
        self.value = ''

    def set_name(self, n):
        self.name = n

    def set_value(self, v):
        self.value = v

    def to_xml(self):
        return '<' + self.name + '>' + self.value + '</' + self.name + '>'


class impuesto:
    def __init__(self):
        self.MontoImpuesto = 0
        self.MontoGravable = 0
        self.CodigoUnidadGravable = 0
        self.NombreCorto = ''

    def set_monto_impuesto(self, monto_imp):
        self.MontoImpuesto = monto_imp

    def set_monto_gravable(self, monto_grav):
        self.MontoGravable = monto_grav

    def set_codigo_unidad_gravable(self, cod_unid_grav):
        self.CodigoUnidadGravable = cod_unid_grav

    def set_nombre_corto(self, nombre_corto_impuesto):
        self.NombreCorto = nombre_corto_impuesto

    def to_xml(self):
        return '<dte:Impuesto>' + '<dte:NombreCorto>' + self.NombreCorto + '</dte:NombreCorto>' + '<dte:CodigoUnidadGravable>' + str(
            self.CodigoUnidadGravable) + '</dte:CodigoUnidadGravable>' + '<dte:MontoGravable>' + str(
            self.MontoGravable) + '</dte:MontoGravable>' + '<dte:MontoImpuesto>' + str(
            self.MontoImpuesto) + '</dte:MontoImpuesto></dte:Impuesto>'


class item:
    def __init__(self):
        self.numero_linea = 0
        self.bien_o_servicio = ''
        self.Cantidad = 0
        self.UnidadMedida = 'UND'
        self.Descripcion = ''
        self.PrecioUnitario = 0
        self.Precio = 0
        self.Descuento = 0
        self.Impuestos = []
        self.Total = 0
        self.xml_plano = ''
        self.es_especial = False

    def set_impuesto(self, imp):
        self.Impuestos.append(imp)

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

    def set_precio(self, precio):
        self.Precio = precio

    def set_descuento(self, descuento):
        self.Descuento = descuento

    def set_total(self, total):
        self.Total = total

    def set_es_especial(self, v):
        self.es_especial = v

    def to_xml(self):
        xml = ''
        xml += '<stdTWS.stdTWSCIt.stdTWSDIt>'
        xml += '<TrnLiNum>' + str(self.numero_linea) + '</TrnLiNum>'
        xml += '<TrnArtCod>10101</TrnArtCod>'
        xml += '<TrnArtNom>' + self.Descripcion + '</TrnArtNom>'
        xml += '<TrnCan>' + str(self.Cantidad) + '</TrnCan>'
        xml += '<TrnVUn> ' + str(self.PrecioUnitario) + ' </TrnVUn>'
        xml += '<TrnUniMed>' + self.UnidadMedida + '</TrnUniMed>'
        xml += '<TrnVDes>' + str(self.Descuento) + '</TrnVDes>'
        xml += '<TrnArtBienSer>' + self.bien_o_servicio + '</TrnArtBienSer>'
        xml += '<TrnArtImpAdiCod>0</TrnArtImpAdiCod>'
        xml += '<TrnArtImpAdiUniGrav>0</TrnArtImpAdiUniGrav>'
        xml += '<TrnDetCampAdi01>ABCD 01</TrnDetCampAdi01>'
        xml += '<TrnDetCampAdi02>ABCD 02</TrnDetCampAdi02>'
        xml += '<TrnDetCampAdi03>ABCD 03</TrnDetCampAdi03>'
        xml += '<TrnDetCampAdi04>ABCD 04</TrnDetCampAdi04>'
        xml += '<TrnDetCampAdi05>ABCD 05</TrnDetCampAdi05>'
        xml += '</stdTWS.stdTWSCIt.stdTWSDIt>'
        return xml


class frase:
    def __init__(self):
        self.exempt = '1'
        self.xml_plano = ''

    def to_xml(self):
        return self.xml_plano

    def set_frase(self, codigo_frase, tipo_frase, numero_resolucion='', fecha_resolucion=''):
        self.xml_plano += '<TrnExento>' + self.exempt + '</TrnExento>'
        self.xml_plano += '<TrnFraseTipo>' + tipo_frase + '</TrnFraseTipo>'
        self.xml_plano += '<TrnEscCod>' + codigo_frase + '</TrnEscCod>'


class fel_dte:
    def __init__(self):
        self.clave_unica = ''
        self.company = False
        self.emisor = EcofacturaEmisor.emisor()
        self.receptor = EcofacturaReceptor.receptor()
        self.frase_fel = frase()
        self.xml_plano = ''
        self.xml_firmado = ''
        self.xml_certificado = ''
        self.datos_emisor = ''
        self.datos_generales = ''
        self.item_list = []
        self.lista_adendas = []
        self.lista_complementos = []
        self.GTDocumento = r'<stdTWS xmlns="FEL">'
        self.exportacion = ''
        self.acceso = ''
        self.tipo_personeria = ''
        self.tipo_especial = ''
        self.codigo_moneda = ''
        self.fecha_hora_emision = ''
        self.tipo_dte = ''
        self.especial_identifier_mode = 'CUI'

    def anular(self, uuid, reason, key_certify, key_sign, user, vat, company):
        self.company = company
        self.xml_plano = ''
        _logger.info('*********************')
        _logger.info(self.xml_plano, 'XML PLANO ANULACION NO EXISTE PARA ECOFACTURAS')
        _logger.info('*********************')
        self.fel_certificacion_response = self.certificar_xml(self.xml_plano, "S", key_certify, key_sign, user, vat,
                                                              uuid=uuid, reason=reason)
        if self.fel_certificacion_response["resultado"]:
            self.certificacion_fel = {"resultado": True, "fecha": self.fel_certificacion_response["fecha"],
                                      "uuid": self.fel_certificacion_response["uuid"],
                                      "serie": self.fel_certificacion_response["serie"],
                                      "numero": self.fel_certificacion_response["numero"], "xml_firmado": '',
                                      "xml_plano": self.xml_plano,
                                      "xml_certificado": self.fel_certificacion_response["xml_certificado"],
                                      "pdf": self.fel_certificacion_response['pdf_cert'],
                                      "descripcion_alertas_infile": self.fel_certificacion_response[
                                          "descripcion_alertas_infile"]}
        else:
            self.certificacion_fel = self.fel_certificacion_response
            self.certificacion_fel["xml_plano"] = self.xml_plano
        return self.certificacion_fel

    def certificar(self, key_certify, key_sign, user, vat, email, company):
        self.company = company
        self.xml_plano += self.GTDocumento
        self.xml_plano += self.emisor.to_xml()
        self.xml_plano += self.xml_datos_generales()
        self.xml_plano += self.receptor.get_nit()
        self.xml_plano += self.get_especial() if self.tipo_dte == 'FESP' or self.tipo_especial == '3' else '' #tipo_especial 3 se refiere a facturas con cédula extranjera
        self.xml_plano += '<TrnExp>' + self.generar_expo() + '</TrnExp>'
        self.xml_plano += self.frase_fel.to_xml() if not self.exportacion else ''
        self.xml_plano += self.receptor.get_purchaser_code() if self.exportacion else ''
        self.xml_plano += self.receptor.to_xml(email)

        if self.lista_adendas:
            for adenda in self.lista_adendas:
                self.xml_plano += adenda.to_xml()

        if self.item_list:
            self.xml_plano += '<stdTWSD>'
            for item in self.item_list:
                self.xml_plano += item.to_xml()
            self.xml_plano += '</stdTWSD>'

        self.xml_plano += self.xml_complementos()
        self.xml_plano += '</stdTWS>'

        _logger.info('*********************')
        _logger.info(self.xml_plano, 'XML PLANO')
        _logger.info('*********************')
        self.certificacion_fel = {}
        self.fel_certificacion_response = self.certificar_xml(self.xml_plano, "N",
                                                              key_certify, key_sign, user, vat)

        if self.fel_certificacion_response["resultado"]:
            self.certificacion_fel = {"resultado": True, "fecha": self.fel_certificacion_response["fecha"],
                                      "uuid": self.fel_certificacion_response["uuid"],
                                      "serie": self.fel_certificacion_response["serie"],
                                      "numero": self.fel_certificacion_response["numero"],
                                      "xml_plano": self.xml_plano, "xml_firmado": '',
                                      'pdf': self.fel_certificacion_response['pdf_cert'],
                                      "xml_certificado": self.fel_certificacion_response["xml_certificado"],
                                      "descripcion_alertas_infile": self.fel_certificacion_response[
                                          "descripcion_alertas_infile"]}
        else:
            self.certificacion_fel = self.fel_certificacion_response
            self.certificacion_fel["xml_plano"] = self.xml_plano
        return self.certificacion_fel

    def agregar_complemento(self, complemento):
        self.lista_complementos.append(complemento)

    def get_especial(self):
        return '<TrnBenConEspecial>' + self.tipo_especial + '</TrnBenConEspecial>'

    def set_tipo_especial(self, especial_identifier_mode):
        self.tipo_especial = especial_identifier_mode

    def set_exportacion(self, exp):
        self.exportacion = exp

    def set_clave_unica(self, clave):
        self.clave_unica = clave

    def xml_complementos(self):
        xml_complemento = ''
        if self.lista_complementos:
            for complemento in self.lista_complementos:
                xml_complemento += complemento.to_xml()
        return xml_complemento

    def generar_expo(self):
        exp = '1' if self.exportacion else '0'
        return exp

    def set_identifier_mode(self, mode):
        """Método para agregar modo de identificación para facturas especiales. Si es DPI/CUI o Pasaporte"""
        self.especial_identifier_mode = mode

    def set_datos_generales(self, codigo_moneda, fecha_hora_emision, tipo_dte):
        self.codigo_moneda = codigo_moneda
        self.fecha_hora_emision = fecha_hora_emision
        self.tipo_dte = tipo_dte

    def xml_datos_generales(self):
        self.datos_generales += '<TipTrnCod>' + self.tipo_dte + '</TipTrnCod>'
        self.datos_generales += '<TrnNum>' + self.clave_unica + '</TrnNum>'
        self.datos_generales += '<TrnFec>' + self.fecha_hora_emision + '</TrnFec>'
        self.datos_generales += '<MonCod>' + self.codigo_moneda + '</MonCod>'
        return self.datos_generales

    def set_datos_emisor(self, emi):
        self.emisor = emi

    def set_datos_receptor(self, rec):
        self.receptor = rec

    def agregar_adenda(self, fel_adenda):
        self.lista_adendas.append(fel_adenda)

    def agregar_item(self, fel_item):
        self.item_list.append(fel_item)

    def _parser_response(self, response):
        """Seccion para parsear el resultado devuelto, para obtener los datos necesarios."""
        tree = ElementTree(fromstring(response))
        root = tree.getroot()
        list_nodes = root.getiterator()
        data = dict()

        for node in list_nodes:
            if node.tag == 'Error':
                value = node.attrib
                value.update({'message': node.text})
            else:
                value = node.attrib or node.text
            data.update({node.tag: value})
        return data

    def certificar_xml(self, xml_plano, anulacion, key, key_sign, user, vat, uuid=False, reason=False):
        try:
            if anulacion != "S":
                # url_cert = 'http://pruebas.ecofactura.com.gt:8080/fel/services/facturacion?wsdl'
                url_cert = self.company.get_url('certify')
            else:
                # url_cert = 'http://pruebas.ecofactura.com.gt:8080/fel/services/facturacion?wsdl'
                url_cert = self.company.get_url('cancel')

            client = Client(url_cert)

            if anulacion != "S":
                response = client.service.Execute(Cliente=key_sign, Usuario=user, Clave=key,
                                                  Nitemisor=vat, Xmldoc=xml_plano)
            else:
                response = client.service.Execute(Cliente=key_sign, Usuario=user, Clave=key, Nitemisor=vat,
                                                  Numautorizacionuuid=uuid, Motivoanulacion=reason)
            data_result = self._parser_response(response)

            if data_result and 'Error' not in data_result:
                values = data_result.get('DTE', {'FechaCertificacion': 'No fue dado una fecha de certificación.',
                                                 'NumeroAutorizacion': 'No fue dado un UUID de certificación.',
                                                 'Serie': 'No fue dado una serie de certificación.',
                                                 'Numero': 'No fue dado un número de certificación.'})
                fel_cert_response = {"resultado": True, "fecha": ustr(values.get('FechaCertificacion')),
                                     "uuid": ustr(values.get('NumeroAutorizacion')),
                                     "serie": ustr(values.get('Serie')),
                                     "numero": ustr(values.get('Numero')),
                                     "xml_plano": xml_plano,
                                     "xml_certificado": ustr(data_result.get('Xml', 'No fue recibido un valor.')),
                                     "pdf_cert": ustr(data_result.get('Pdf', False)),
                                     "descripcion_alertas_infile": []}
            else:
                error_values = data_result.get('Error', {'message': 'No fue dado un mensaje específico del error.',
                                                         'Codigo': 'No fue dado un código específico del error.'})
                fel_cert_response = {
                    'resultado': False,
                    "descripcion_errores": [{
                        "mensaje_error": ustr(error_values.get('message')),
                        "fuente": '', "categoria": 'ERROR DE COMUNICACIÓN',
                        "numeral": ustr(error_values.get('Codigo')),
                        "validacion": ''
                    }], 'archivo': 'Hubo un error (excepción) en la comunicación.',
                    'descripcion': ustr(error_values.get('message'))
                }
        except IncompleteOperation as incomplete:
            fel_cert_response = {
                'resultado': False,
                "descripcion_errores": [{
                    "mensaje_error": ustr(incomplete), "fuente": '',
                    "categoria": 'ERROR DE COMUNICACIÓN POR OPERACIÓN INCOMPLETA', "numeral": '#', "validacion": ''
                }], 'archivo': 'Hubo un error (excepción) en la comunicación.',
                'descripcion': ustr(incomplete)
            }
        except TransportError as status_error:
            fel_cert_response = {
                'resultado': False,
                "descripcion_errores": [{
                    "mensaje_error": ustr(status_error), "fuente": '',
                    "categoria": 'ERROR DE COMUNICACIÓN POR FALLO EN ENVÍO DE DATOS', "numeral": '#', "validacion": ''
                }], 'archivo': 'Hubo un error (excepción) en la comunicación.',
                'descripcion': ustr(status_error)
            }
        except Exception as e:
            """Actualizaciones del 09.09.2021
                Mejoras para manejar errores luego de certificaciones FEL
            """
            _logger.error('Error al realizar el consumo del servicio para certificar de documento FEL: ' + ustr(e))
            fel_cert_response = {
                'resultado': False,
                "descripcion_errores": [{
                    "mensaje_error": ustr(e), "fuente": '',
                    "categoria": 'ERROR DE COMUNICACIÓN GENERAL', "numeral": '#', "validacion": ''
                }], 'archivo': 'Hubo un error (excepción) en la comunicación.',
                'descripcion': ustr(e)
            }

        return fel_cert_response
