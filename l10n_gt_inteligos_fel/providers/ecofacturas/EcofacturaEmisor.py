
class emisor:
    def __init__(self):
        self.datos_emisor = ""
        self.xml_plano = ""

    def to_xml(self):
        return self.datos_emisor

    def set_datos_emisor(self, afiliacion_iva, codigo_establecimiento,
                         correo_emisor, nit_emisor, nombre_comercial, nombre_emisor):
        self.datos_emisor += '<TrnEstNum>' + codigo_establecimiento + '</TrnEstNum>'
