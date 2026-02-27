
class emisor:
    def __init__(self):
        self.datos_emisor = ""
        self.direccion = ""
        self.xml_plano = ""

    def to_xml(self):
        return self.datos_emisor + self.direccion + '</dte:Emisor>'

    def set_direccion(self, direc, codigo_postal, municipio, departamento, pais):
        self.direccion += '<dte:DireccionEmisor>'
        self.direccion += '<dte:Direccion>' + direc + '</dte:Direccion>'
        self.direccion += '<dte:CodigoPostal>' + codigo_postal + '</dte:CodigoPostal>'
        self.direccion += '<dte:Municipio>' + municipio + '</dte:Municipio>'
        self.direccion += '<dte:Departamento>' + departamento + '</dte:Departamento>'
        self.direccion += '<dte:Pais>' + pais + '</dte:Pais>'
        self.direccion += '</dte:DireccionEmisor>'

    def set_datos_emisor(self, afiliacion_iva, codigo_establecimiento,
                         correo_emisor, nit_emisor, nombre_comercial, nombre_emisor):
        self.datos_emisor = '<dte:Emisor AfiliacionIVA="' + afiliacion_iva + '" CodigoEstablecimiento="' + codigo_establecimiento \
                            + '" CorreoEmisor="' + correo_emisor + '" NITEmisor="' + nit_emisor + '" NombreComercial="' + nombre_comercial \
                            + '" NombreEmisor="' + nombre_emisor + \
                            '">'
