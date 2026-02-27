
class receptor:
    def __init__(self):
        self.datos_receptor = ""
        self.direccion = ""
        self.xml_plano = ""
        self.correo = ''
        self.id_receptor = ''
        self.nombre_receptor = ''
        self.purchaser_code = None

    def to_xml(self, email_emisor):
        """Método para obtener la información general del receptor (cliente)"""
        return self.datos_receptor + self.direccion + '<TrnObs>0</TrnObs>' + self.get_email(email_emisor)

    def set_direccion(self, direc, codigo_postal, municipio, departamento, pais):
        self.direccion += '<TrnEFACECliDir>' + direc + ', ' + municipio + ', ' \
                          + departamento + ', ' + pais + '</TrnEFACECliDir>'

    def get_nit(self):
        """Método para obtener la información NIT del receptor (cliente)"""
        return '<TrnBenConNIT>' + self.id_receptor + '</TrnBenConNIT>'

    def get_email(self, email_emisor):
        """Método para obtener la información de correo(s) a notificar (receptor y/o emisor)"""
        extra_email = (';' + email_emisor) or ''
        return '<TrnEmail>' + self.correo + extra_email + '</TrnEmail>'

    def set_purchaser_code(self, code):
        """Método para agregar la información del código
            de exportación del comprador cuando es un documento de exportación
        """
        self.purchaser_code = code

    def get_purchaser_code(self):
        """Método para obtener la información del código
            de exportación del comprador cuando es un documento de exportación
        """
        return '<TrnEFACECliCod>' + self.purchaser_code + '</TrnEFACECliCod>'

    def set_datos_receptor(self, correo_receptor, id_receptor, nombre_receptor):
        self.correo = correo_receptor
        self.id_receptor = id_receptor
        self.nombre_receptor = nombre_receptor
        self.datos_receptor += '<TrnEFACECliNom>' + nombre_receptor + '</TrnEFACECliNom>'
