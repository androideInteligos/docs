class receptor:
    def __init__(self):
        self.datos_receptor = ""
        self.direccion = ""
        self.xml_plano = ""
        self.tipo_especial = ""
        self.correo = ''
        self.id_receptor = ''
        self.nombre_receptor = ''

    def to_xml(self):
        return self.datos_receptor + self.direccion + '</dte:Receptor>'

    def set_especial(self, tipo_esp):
        self.datos_receptor = '<dte:Receptor CorreoReceptor="' + self.correo + '" TipoEspecial="' + tipo_esp + \
                              '" IDReceptor="' + self.id_receptor + '" NombreReceptor="' + self.nombre_receptor + \
                              '">'

    def set_direccion(self, direc, codigo_postal, municipio, departamento, pais):
        self.direccion += '<dte:DireccionReceptor>'
        self.direccion += '<dte:Direccion>' + direc + '</dte:Direccion>'
        self.direccion += '<dte:CodigoPostal>' + codigo_postal + '</dte:CodigoPostal>'
        self.direccion += '<dte:Municipio>' + municipio + '</dte:Municipio>'
        self.direccion += '<dte:Departamento>' + departamento + '</dte:Departamento>'
        self.direccion += '<dte:Pais>' + pais + '</dte:Pais>'
        self.direccion += '</dte:DireccionReceptor>'

    def set_datos_receptor(self, correo_receptor, id_receptor, nombre_receptor):
        self.correo = correo_receptor
        self.id_receptor = id_receptor
        self.nombre_receptor = nombre_receptor
        self.datos_receptor = '<dte:Receptor CorreoReceptor="' + correo_receptor + '" IDReceptor="' \
                              + id_receptor + '" NombreReceptor="' + nombre_receptor + \
                              '">'
