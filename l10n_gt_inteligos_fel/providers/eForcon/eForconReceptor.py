# -*- coding: utf-8 -*-


class receptor:
    def __init__(self):
        self.datos_receptor = ""
        self.xml_plano = ""

    def to_xml(self):
        return self.datos_receptor

    def set_datos_receptor(self, id_receptor, nombre_receptor, correo_receptor, correo_receptor_cc,
                           direc, codigo_postal, municipio, departamento, pais, tipo_receptor='N'):
        self.datos_receptor += '<tipoReceptor>' + tipo_receptor + '</tipoReceptor>'
        self.datos_receptor += '<idReceptor>' + id_receptor + '</idReceptor>'
        self.datos_receptor += '<nombreReceptor>' + nombre_receptor + '</nombreReceptor>'
        # self.datos_receptor += '<correoReceptor>' + correo_receptor + '</correoReceptor>'
        # self.datos_receptor += '<copiarCorreoReceptor>' + correo_receptor_cc + '</copiarCorreoReceptor>'
        self.datos_receptor += '<correoReceptor></correoReceptor>'
        self.datos_receptor += '<copiarCorreoReceptor></copiarCorreoReceptor>'
        self.datos_receptor += '<direccionReceptor>' + direc + '</direccionReceptor>'
        self.datos_receptor += '<codigoPostalReceptor>' + codigo_postal + '</codigoPostalReceptor>'
        self.datos_receptor += '<municipioReceptor>' + municipio + '</municipioReceptor>'
        self.datos_receptor += '<departamentoReceptor>' + departamento + '</departamentoReceptor>'
        self.datos_receptor += '<paisReceptor>' + pais + '</paisReceptor>'
