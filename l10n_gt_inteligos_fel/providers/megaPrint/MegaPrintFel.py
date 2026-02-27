# -*- coding: utf-8 -*-

import requests
from xml.etree.ElementTree import fromstring, ElementTree
from . import MegaPrintEmisor
from . import MegaPrintReceptor
from odoo.tools import ustr


class complemento_notas():
    def __init__(self):
        self.xml = ''
        self.lista_complementos = []

    def agregar(self, RegimenAntiguo, MotivoAjuste, FechaEmisionDocumentoOrigen, SerieDocumentoOrigen,
                NumeroAutorizacionDocumentoOrigen, NumeroDocumentoOrigen):
        self.lista_complementos.append({
            "RegimenAntiguo": RegimenAntiguo,
            "MotivoAjuste": MotivoAjuste,
            "FechaEmisionDocumentoOrigen": FechaEmisionDocumentoOrigen,
            "NumeroDocumentoOrigen": NumeroDocumentoOrigen,
            "SerieDocumentoOrigen": SerieDocumentoOrigen,
            "NumeroAutorizacionDocumentoOrigen": NumeroAutorizacionDocumentoOrigen
        })

    def to_xml(self):
        self.xml = ''
        if len(self.lista_complementos) > 0:

            # revisar etiqueta con notas de credito xml
            self.xml += '<dte:Complemento IDComplemento="text" NombreComplemento="GT_Complemento_Referencia_Nota-0.1.0" URIComplemento="GT_Complemento_Referencia_Nota-0.1.0.xsd">'

            for complemento in self.lista_complementos:
                if complemento["RegimenAntiguo"] == 'ANTIGUO':
                    self.xml += '<cno:ReferenciasNota xmlns:cno="http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0" RegimenAntiguo="Antiguo" FechaEmisionDocumentoOrigen="' + str(
                        complemento["FechaEmisionDocumentoOrigen"]) + '" MotivoAjuste="' + str(
                        complemento["MotivoAjuste"]) + '" NumeroAutorizacionDocumentoOrigen="' + str(
                        complemento["NumeroAutorizacionDocumentoOrigen"]) + '" NumeroDocumentoOrigen="' + str(
                        complemento["NumeroDocumentoOrigen"]) + '" SerieDocumentoOrigen="' + str(
                        complemento["SerieDocumentoOrigen"]) + '" Version="1" />'
                else:
                    self.xml += '<cno:ReferenciasNota xmlns:cno="http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0" FechaEmisionDocumentoOrigen="' + str(
                        complemento["FechaEmisionDocumentoOrigen"]) + '" MotivoAjuste="' + str(
                        complemento["MotivoAjuste"]) + '" NumeroAutorizacionDocumentoOrigen="' + str(
                        complemento["NumeroAutorizacionDocumentoOrigen"]) + '" NumeroDocumentoOrigen="' + str(
                        complemento["NumeroDocumentoOrigen"]) + '" SerieDocumentoOrigen="' + str(
                        complemento["SerieDocumentoOrigen"]) + '" Version="1" />'

            self.xml += '</dte:Complemento>'
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
            self.xml += '<dte:Complemento IDComplemento="1" NombreComplemento="EXPORTACION" URIComplemento="http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0">'

            for complemento in self.lista_complementos:
                self.xml += '<cex:Exportacion xmlns:cex="http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0" Version="1">'
                self.xml += '<cex:LugarExpedicion>' + str(complemento["LugarExpedicion"]) + '</cex:LugarExpedicion>'
                self.xml += '<cex:NombreConsignatarioODestinatario>' + str(
                    complemento["NombreConsignatarioODestinatario"]) + '</cex:NombreConsignatarioODestinatario>'
                self.xml += '<cex:DireccionConsignatarioODestinatario>' + str(
                    complemento["DireccionConsignatarioODestinatario"]) + '</cex:DireccionConsignatarioODestinatario>'
                self.xml += '<cex:CodigoConsignatarioODestinatario>' + str(
                    complemento["CodigoConsignatarioODestinatario"]) + '</cex:CodigoConsignatarioODestinatario>'
                self.xml += '<cex:NombreComprador>' + str(complemento["NombreComprador"]) + '</cex:NombreComprador>'
                self.xml += '<cex:DireccionComprador>' + str(
                    complemento["DireccionComprador"]) + '</cex:DireccionComprador>'
                self.xml += '<cex:CodigoComprador>' + str(complemento["CodigoComprador"]) + '</cex:CodigoComprador>'
                self.xml += '<cex:PaisConsignatario>' + str(
                    complemento["PaisConsignatario"]) + '</cex:PaisConsignatario>'
                self.xml += '<cex:OtraReferencia>' + str(complemento["OtraReferencia"]) + '</cex:OtraReferencia>'
                self.xml += '<cex:INCOTERM>' + str(complemento["INCOTERM"]) + '</cex:INCOTERM>'
                # self.xml += '<cex:NombreExportador>' + str(complemento["NombreExportador"]) + '</cex:NombreExportador>'
                self.xml += '<cex:CodigoExportador>' + str(complemento["CodigoExportador"]) + '</cex:CodigoExportador>'
                self.xml += '</cex:Exportacion>'
            self.xml += '</dte:Complemento>'

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
        if len(self.lista_complementos) > 0:
            self.xml += '<dte:Complemento IDComplemento="text" NombreComplemento="GT_Complemento_Fac_Especial" URIComplemento="GT_Complemento_Fac_Especial.xsd">'
            for complemento in self.lista_complementos:
                self.xml += '<cfe:RetencionesFacturaEspecial xmlns:cfe="http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0" Version="1">'
                self.xml += '<cfe:RetencionISR>' + str(complemento["RetencionISR"]) + '</cfe:RetencionISR>'
                self.xml += '<cfe:RetencionIVA>' + str(complemento["RetencionIVA"]) + '</cfe:RetencionIVA>'
                self.xml += '<cfe:TotalMenosRetenciones>' + str(
                    complemento["TotalMenosRetenciones"]) + '</cfe:TotalMenosRetenciones>'
                self.xml += '</cfe:RetencionesFacturaEspecial>'

            self.xml += '</dte:Complemento>'

        return self.xml


class complemento_cambiaria():
    def __init__(self):
        self.xml = ''
        self.lista_complementos = []

    def to_xml(self):
        self.xml = ''
        if len(self.lista_complementos) > 0:
            self.xml += '<dte:Complemento IDComplemento="1" NombreComplemento="Abono" URIComplemento="http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0">'
            for complemento in self.lista_complementos:
                self.xml += '<cfc:AbonosFacturaCambiaria xmlns:cfc="http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0" Version="1">'
                self.xml += '<cfc:Abono>'
                self.xml += '<cfc:NumeroAbono>' + str(complemento["numero_abono"]) + '</cfc:NumeroAbono>'
                self.xml += '<cfc:FechaVencimiento>' + str(complemento["fecha_vencimiento"]) + '</cfc:FechaVencimiento>'
                self.xml += '<cfc:MontoAbono>' + str(complemento["monto_abono"]) + '</cfc:MontoAbono>'
                self.xml += '</cfc:Abono>'
                self.xml += '</cfc:AbonosFacturaCambiaria>'

            self.xml += '</dte:Complemento>'

        return self.xml

    def agregar(self, num_abono, fec_vencimiento, mon_abono):
        self.lista_complementos.append(
            {"numero_abono": num_abono, "fecha_vencimiento": fec_vencimiento, "monto_abono": mon_abono})


class adenda:
    def __init__(self):
        self.nombre = ''
        self.valor = ''

    def set_nombre(self, n):
        self.nombre = n

    def set_valor(self, v):
        self.valor = v

    def to_xml(self):
        item_count = 0
        value_count = 0
        xml = ''
        if type(self.valor) != list:
            xml = '<' + self.nombre + '>' + self.valor + '</' + self.nombre + '>'
        elif type(self.valor) == list:
            for value in self.valor:
                item_count += 1
                xml += '<AdendaItem LineaReferencia="' + str(item_count) + '">'
                xml += '<Valor' + str(1) + '>' + value + '</Valor' + str(1) + '>'
                xml += '</AdendaItem>'
        return xml


class total_impuesto:
    def __init__(self):
        self.nombre_corto = ''
        self.total_monto_impuesto = 0

    def set_nombre_corto(self, nc):
        self.nombre_corto = nc

    def set_total_monto_impuesto(self, t):
        self.total_monto_impuesto = t


class totales:
    def __init__(self):
        self.lista_total_impuesto = []
        self.gran_total = 0

    def set_gran_total(self, gran_tot):
        self.gran_total = gran_tot

    def set_total_impuestos(self, lista_total):
        self.lista_total_impuesto.append(lista_total)

    def to_xml(self):
        xml = ''
        xml += '<dte:Totales>'

        if len(self.lista_total_impuesto) > 0:
            xml += '      <dte:TotalImpuestos>'
            for total_impuesto in self.lista_total_impuesto:
                xml += '      <dte:TotalImpuesto NombreCorto="' + total_impuesto.nombre_corto + '" TotalMontoImpuesto="' + str(
                    total_impuesto.total_monto_impuesto) + '"></dte:TotalImpuesto>'

            xml += '    </dte:TotalImpuestos>'
        xml += '    <dte:GranTotal>' + str(self.gran_total) + '</dte:GranTotal>'
        xml += '  </dte:Totales>'
        return xml


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
        self.otro_descuento = 0
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

    def set_otro_descuento(self, otro_descuento):
        self.otro_descuento = otro_descuento

    def set_total(self, total):
        self.Total = total

    def set_es_especial(self, v):
        self.es_especial = v

    def to_xml(self):
        xml = ''
        xml += '<dte:Item BienOServicio="' + self.bien_o_servicio + '" NumeroLinea="' + str(self.numero_linea) + '">'
        xml += '<dte:Cantidad>' + str(self.Cantidad) + '</dte:Cantidad>'
        xml += '      <dte:UnidadMedida>' + self.UnidadMedida + '</dte:UnidadMedida>'
        xml += '      <dte:Descripcion>' + self.Descripcion + '</dte:Descripcion>'
        xml += '      <dte:PrecioUnitario>' + str(self.PrecioUnitario) + '</dte:PrecioUnitario>'
        xml += '      <dte:Precio>' + str(self.Precio) + '</dte:Precio>'
        xml += '      <dte:Descuento>' + str(self.Descuento) + '</dte:Descuento>'

        if self.otro_descuento:
            xml += '      <dte:OtrosDescuento>' + str(self.otro_descuento) + '</dte:OtrosDescuento>'

        if len(self.Impuestos) > 0:
            xml += '      <dte:Impuestos>'
            for impuesto_fel in self.Impuestos:
                xml += impuesto_fel.to_xml()
            xml += '      </dte:Impuestos>'

        xml += '      <dte:Total>' + str(self.Total) + '</dte:Total>'
        xml += '    </dte:Item>'
        return xml


class frase:
    def __init__(self):
        self.codigo = ''
        self.tipo = ''
        self.xml_plano = ''

    def to_xml(self):
        if len(self.xml_plano) > 0:
            return '<dte:Frases>' + self.xml_plano + '</dte:Frases>'
        else:
            return ""

    def set_frase(self, codigo_frase, tipo_frase, numero_resolucion='', fecha_resolucion=''):
        texto_numero_resolucion = ''
        texto_fecha_resolucion = ''

        if len(numero_resolucion) > 0:
            texto_numero_resolucion = ' NumeroResolucion="' + numero_resolucion + '" '

        if len(fecha_resolucion) > 0:
            texto_fecha_resolucion = ' FechaResolucion="' + fecha_resolucion + '" '
        # revisar si se puede utilizar lal inea ya que es extra
        self.xml_plano += '<dte:Frase CodigoEscenario="' + codigo_frase + '" TipoFrase="' + tipo_frase + '" ' + texto_numero_resolucion + texto_fecha_resolucion + '></dte:Frase>'


class fel_dte:
    def __init__(self):
        self.clave_unica = ''
        self.company = False
        self.emisor = MegaPrintEmisor.emisor()
        self.receptor = MegaPrintReceptor.receptor()
        self.frase_fel = frase()
        self.totales_fel = totales()
        self.xml_plano = ''
        self.xml_firmado = ''
        self.xml_certificado = ''
        self.datos_emisor = ''
        self.datos_generales = ''
        self.item_list = []
        self.lista_adendas = []
        self.lista_complementos = []
        self.GTDocumento = r'<dte:GTDocumento xmlns:dte="http://www.sat.gob.gt/dte/fel/0.2.0" Version="0.1">'
        self.SAT = '<dte:SAT ClaseDocumento="dte">'
        self.exportacion = ''
        self.acceso = ''
        self.tipo_personeria = ''
        self.tipo_especial = ''
        self.codigo_moneda = ''
        self.fecha_hora_emision = ''
        self.tipo_dte = ''
        self.has_list = False

    def anular(self, fecha_hora_anulacion, nit_emisor, fecha_emision_documento_anular, id_receptor,
               numero_documento_anular, motivo_anulacion, token, company):
        self.company = company
        self.xml_plano = ''
        self.xml_plano += '<?xml version="1.0" encoding="UTF-8"?>'
        self.xml_plano += '<ns:GTAnulacionDocumento xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:ns="http://www.sat.gob.gt/dte/fel/0.1.0" Version="0.1">'
        self.xml_plano += '<ns:SAT>'
        self.xml_plano += '<ns:AnulacionDTE ID="DatosCertificados">'
        self.xml_plano += '<ns:DatosGenerales FechaHoraAnulacion="' + fecha_hora_anulacion + '" ID="DatosAnulacion" NITEmisor="' + nit_emisor + '" FechaEmisionDocumentoAnular="' + fecha_emision_documento_anular + '" IDReceptor="' + id_receptor + '" NumeroDocumentoAAnular="' + numero_documento_anular + '" MotivoAnulacion="' + motivo_anulacion + '"/>'
        self.xml_plano += '</ns:AnulacionDTE>'
        self.xml_plano += '</ns:SAT>'
        self.xml_plano += '</ns:GTAnulacionDocumento>'

        print('*********************')
        print(self.xml_plano)
        print('*********************')

        self.fel_firma_response = self.firmar_xml(self.xml_plano, "S", token)
        if self.fel_firma_response["resultado"]:
            self.xml_firmado = self.fel_firma_response["archivo"]
            self.fel_certificacion_response = self.certificar_xml(self.xml_firmado, "S", token)
            if self.fel_certificacion_response["resultado"]:
                self.certificacion_fel = {"resultado": True, "fecha": fecha_hora_anulacion,
                                          "uuid": "Anulacion no registra UUID",
                                          "serie": "Anulacion no registra serie",
                                          "numero": "Anulacion no registra numero",
                                          "xml_firmado": self.xml_firmado,
                                          "xml_certificado": self.fel_certificacion_response["xml_certificado"]}
            else:
                self.certificacion_fel = self.fel_certificacion_response
        else:
            self.certificacion_fel = {
                "resultado": False, "descripcion": "XML no pudo ser firmado, reintente",
                "sign_response": self.fel_firma_response
            }
        self.certificacion_fel.update({"xml_plano": self.xml_plano})
        return self.certificacion_fel

    def certificar(self, token, company):
        self.company = company
        self.xml_plano += self.GTDocumento
        self.xml_plano += self.SAT
        self.xml_plano += '<dte:DTE ID="DatosCertificados">'
        self.xml_plano += '<dte:DatosEmision ID="DatosEmision">'
        self.xml_plano += self.xml_datos_generales()  # self.datos_generales  #hay que ver como se mete el numero de acceso
        self.xml_plano += self.datos_emisor
        self.xml_plano += self.emisor.to_xml()
        self.xml_plano += self.receptor.to_xml()
        self.xml_plano += self.frase_fel.to_xml()

        self.certificacion_fel = {}
        if len(self.item_list) > 0:
            self.xml_plano += '<dte:Items>'
            for item in self.item_list:
                self.xml_plano += item.to_xml()
            self.xml_plano += '</dte:Items>'

        self.xml_plano += self.totales_fel.to_xml()
        self.xml_plano += self.xml_complementos()
        self.xml_plano += '</dte:DatosEmision>'
        self.xml_plano += '</dte:DTE>'

        if len(self.lista_adendas) > 0:
            self.xml_plano += '<dte:Adenda>'
            self.xml_plano += '<dte:AdendaDetail  id="AdendaSummary">'
            self.xml_plano += '<dte:AdendaSummary>'
            for adenda in self.lista_adendas:
                if type(adenda.valor) != list:
                    self.xml_plano += adenda.to_xml()
                elif type(adenda.valor) == list:
                    self.has_list = True
            self.xml_plano += '</dte:AdendaSummary>'
# --------------------Para el envío de adendas de tipo listado
            if self.has_list:
                self.xml_plano += '<dte:AdendaItems>'
                for adenda in self.lista_adendas:
                    if type(adenda.valor) == list:
                        self.xml_plano += adenda.to_xml()
                self.xml_plano += '</dte:AdendaItems>'
            self.xml_plano += '</dte:AdendaDetail>'
#-------------------------fin otras adendas

            # Plantillas para facturas de exportación colocadas de forma estática TODO: Se debe de crear un diseño para clientes futuros para que se pueda enviar la plantilla de forma dinámica
            if self.exportacion != '' and self.tipo_dte == 'FACT':
                self.xml_plano += '<TemplateInfo  detailTemplateId="13502" templateId="13502"/>'
            elif self.exportacion != '' and self.tipo_dte == 'FCAM':
                self.xml_plano += '<TemplateInfo  detailTemplateId="13503" templateId="13503"/>'

            self.xml_plano += '</dte:Adenda>'

        self.xml_plano += '</dte:SAT>'
        self.xml_plano += '</dte:GTDocumento>'
        self.fel_firma_response = self.firmar_xml(self.xml_plano, "N", token)
        if self.fel_firma_response["resultado"]:
            self.xml_firmado = self.fel_firma_response["archivo"]
            self.fel_certificacion_response = self.certificar_xml(self.xml_firmado, "N", token)
            if self.fel_certificacion_response["resultado"]:
                self.certificacion_fel = {"resultado": True, "fecha": self.fecha_hora_emision,
                                          "uuid": self.fel_certificacion_response["uuid"],
                                          "serie": self.fel_certificacion_response["serie"],
                                          "numero": self.fel_certificacion_response["numero"],
                                          "xml_firmado": self.xml_firmado,
                                          "xml_certificado": self.fel_certificacion_response["xml_certificado"]}
            else:
                self.certificacion_fel = self.fel_certificacion_response
        else:
            self.certificacion_fel = {
                "resultado": False, "descripcion": "XML no pudo ser firmado, reintente",
                "sign_response": self.fel_firma_response
            }
        self.certificacion_fel.update({"xml_plano": self.xml_plano})
        return self.certificacion_fel

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
        if len(self.lista_complementos) > 0:
            xml_complemento += '<dte:Complementos>'
            for complemento in self.lista_complementos:
                xml_complemento += complemento.to_xml()
            xml_complemento += '</dte:Complementos>'
        return xml_complemento

    def generar_expo(self):
        print("EN LA EXPORTACION .................................." + str(len(self.exportacion)))
        retorno = ''
        if len(self.exportacion) > 0:
            retorno = 'Exp="' + self.exportacion + '"'
        return retorno

    def generar_acceso(self):
        retorno = ''
        if len(self.acceso) > 0:
            retorno = ' NumeroAcceso="' + self.acceso + '"'
        return retorno

    def generar_tipo_personeria(self):
        retorno = ''
        if len(self.tipo_personeria) > 0:
            retorno = ' TipoPersoneria="' + self.tipo_personeria + '"'
        return retorno

    def set_datos_generales(self, codigo_moneda, fecha_hora_emision, tipo_dte):
        self.codigo_moneda = codigo_moneda
        self.fecha_hora_emision = fecha_hora_emision
        self.tipo_dte = tipo_dte

    def xml_datos_generales(self):
        self.datos_generales = '<dte:DatosGenerales CodigoMoneda="' + self.codigo_moneda + '" ' + self.generar_expo() + ' FechaHoraEmision="' + self.fecha_hora_emision + '"' + self.generar_acceso() + ' Tipo="' + self.tipo_dte + '"' + self.generar_tipo_personeria() + '></dte:DatosGenerales>'
        return self.datos_generales

    def set_datos_emisor(self, emi):
        self.emisor = emi

    def set_datos_receptor(self, rec):
        self.receptor = rec

    def agregar_adenda(self, fel_adenda):
        self.lista_adendas.append(fel_adenda)

    def agregar_item(self, fel_item):
        self.item_list.append(fel_item)

    def agregar_totales(self, fel_totales):
        self.totales_fel = fel_totales

    def access_number(self):
        counter_access_number = self.company.counter_access_number
        if counter_access_number <= 9999999:
            access_number = counter_access_number + 1
            self.company.counter_access_number += 1
            """--------------"""
            return access_number
        else:
            """Actualizaciones del 09.09.2021
                Mejoras para manejar errores luego de certificaciones FEL
            """
            access_number = 1000000
            self.company.counter_access_number = 1
            return access_number

    def _parser_mistakes(self, response):
        tree = ElementTree(fromstring(response))
        root = tree.getroot()
        datadict = {element.tag: element.text for element in root if element.tag != 'listado_errores'}
        datadict.update({section.tag: section.text for element in root for error in element for section in error if
                         element.tag == 'listado_errores'})
        return datadict

    def _parser_response(self, response):
        """Seccion para parsear xml firmado devuelto, para obtener los datos necesarios."""
        tree = ElementTree(fromstring(response))
        root = tree.getroot()

        list_nodes = root.iter()

        data = ''
        for node in list_nodes:
            if node.tag == 'xml_dte':
                data += node.text
        """---------Fin de seccion-------"""
        return data

    def _get_cert_values(self, response):
        tree = ElementTree(fromstring(response))
        root = tree.getroot()
        datadict = {}
        for node in root:
            if node.tag == "{http://www.sat.gob.gt/dte/fel/0.2.0}SAT":
                for subnode in node:
                    if subnode.tag == "{http://www.sat.gob.gt/dte/fel/0.2.0}DTE":
                        for element in subnode:
                            if element.tag == "{http://www.sat.gob.gt/dte/fel/0.2.0}Certificacion":
                                for section in element:
                                    if section.tag == "{http://www.sat.gob.gt/dte/fel/0.2.0}NumeroAutorizacion":
                                        datadict.update({'uuid': section.text})
                                        attrs = {}
                                        for k, v in section.attrib.items():
                                            if k == 'Numero':
                                                attrs.update({'numero': v})
                                            if k == 'Serie':
                                                attrs.update({'serie': v})
                                        datadict.update(attrs)
        return datadict

    def firmar_xml(self, xml_plano, anulacion, token):
        # UrlFirma = 'https://api.soluciones-mega.com/api/solicitaFirma'
        UrlFirma = self.company.get_url('sign')
        container = """<?xml version="1.0" encoding="UTF-8"?><FirmaDocumentoRequest id=""" + '"' + str(
            self.clave_unica) + '"' + """> 
                        <xml_dte><![CDATA[""" + xml_plano + """]]></xml_dte>
                        </FirmaDocumentoRequest>
                    """

        data = container
        headers = {
            'Authorization': "bearer " + token,
            'Content-Type': 'application/xml; charset=utf-8'
        }

        #  CAMBIO PARA CONTINGENCIAS
        access_number = False
        r = False
        fel_firma_response = {'resultado': False}

        try:
            r = requests.post(url=UrlFirma, data=data.encode('utf-8'), headers=headers)
        except requests.exceptions.Timeout:
            access_number = self.access_number()
        except Exception as e:
            """Actualizaciones del 09.09.2021
                Mejoras para manejar errores luego de certificaciones FEL
            """
            fel_firma_response.update({'sign_response': ustr(e)})
            return fel_firma_response

        mistakes = self._parser_mistakes(r.text)

        if r.status_code in [522, 524]:
            access_number = self.access_number()
        #  CAMBIO PARA CONTINGENCIAS

        if not mistakes.get("desc_error"):
            data = self._parser_response(r.text)
            fel_firma_response.update({'archivo': data, 'resultado': True})
        else:
            fel_firma_response.update({'sign_response': mistakes.get("desc_error")})

        if access_number:
            fel_firma_response.update({'access_number': access_number, 'resultado': False})
        return fel_firma_response

    def certificar_xml(self, xml_firmado, anulacion, token):
        if anulacion != "S":
            # url_cert = 'https://apiv2.ifacere-fel.com/api/registrarDocumentoXML'
            url_cert = self.company.get_url('certify')
            data = """<?xml version="1.0" encoding="UTF-8"?> <RegistraDocumentoXMLRequest id=""" + '"' + str(
                self.clave_unica) + '"' + """> 
                                    <xml_dte><![CDATA[""" + xml_firmado + """]]></xml_dte>
                                    </RegistraDocumentoXMLRequest>
                                """
        else:
            # url_cert = 'https://apiv2.ifacere-fel.com/api/anularDocumentoXML'
            url_cert = self.company.get_url('cancel')
            data = """<?xml version="1.0" encoding="UTF-8"?><AnulaDocumentoXMLRequest id=""" + '"' + str(
                self.clave_unica) + '"' + """>
                                <xml_dte><![CDATA[""" + xml_firmado + """]]></xml_dte>
                                </AnulaDocumentoXMLRequest>"""

        headers = {
            'Authorization': "bearer " + token,
            'Content-Type': 'application/xml; charset=utf-8'
        }

        #  CAMBIO PARA CONTINGENCIAS
        access_number = False
        r = False
        fel_cert_response = {'resultado': False}

        try:
            r = requests.post(url=url_cert, data=data.encode('utf-8'), headers=headers)
        except requests.exceptions.Timeout:
            access_number = self.access_number()
        except Exception as e:
            """Actualizaciones del 09.09.2021
                Mejoras para manejar errores luego de certificaciones FEL
            """
            fel_cert_response.update({
                "descripcion_errores": [{
                    "mensaje_error": ustr(e), "fuente": '',
                    "categoria": 'ERROR DE COMUNICACIÓN', "numeral": '#', "validacion": ''
                }], 'archivo': 'Hubo un error en la comunicación.',
                'descripcion': ustr(e)
            })
            return fel_cert_response

        if r.status_code in [522, 524]:
            access_number = self.access_number()
        #  CAMBIO PARA CONTINGENCIAS
        response = r.text

        mistakes = self._parser_mistakes(response)
        if not mistakes.get("desc_error"):
            data = self._parser_response(response)
            fel_cert_response.update({
                'archivo': data,
                'xml_certificado': response
            })
            if anulacion != "S":
                cert_values = self._get_cert_values(data)
                if cert_values:
                    fel_cert_response.update(cert_values)
                    fel_cert_response.update({'resultado': True})
            else:
                fel_cert_response.update({'resultado': True})
        else:
            fel_cert_response.update({
                "descripcion_errores": [{
                    "mensaje_error": mistakes.get("desc_error"), "fuente": '',
                    "categoria": '', "numeral": mistakes.get("tipo_respuesta"), "validacion": ''
                }], 'archivo': 'Hubo un error en los datos enviados.',
                'descripcion': mistakes.get("cod_error")
            })

        #  CAMBIO PARA CONTINGENCIAS
        if access_number:
            fel_cert_response.update({'access_number': access_number})
        return fel_cert_response
