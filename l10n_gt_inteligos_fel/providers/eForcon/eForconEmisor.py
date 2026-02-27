# -*- coding: utf-8 -*-

class emisor:
    def __init__(self):
        self.datos_emisor = ""
        self.xml_plano = ""

    def to_xml(self):
        return self.datos_emisor

    def set_datos_emisor(self, nit_emisor, codigo_establecimiento):
        self.datos_emisor += '<nitEmisor>' + nit_emisor + '</nitEmisor>'
        self.datos_emisor += '<numeroEstablecimiento>' + codigo_establecimiento + '</numeroEstablecimiento>'
