# -*- coding: utf-8 -*-
{
    'name': "Generico - Contabilidad Guatemala",
    'summary': """
        Tropicalización de Inteligos para Guatemala.""",
    'description': """
        Tipos de Documento
        Impuestos
        Datos fiscales en facturas
        Posiciones Fiscales
    """,
    'author': "Proyectos Ágiles, S. A. - Inteligos",
    'website': "https://www.inteligos.gt",
    'category': 'Accounting/Localizations/Account Charts',
    'version': '18.0',
    'depends': ['base', 'account', 'account_accountant', 'l10n_latam_base', 'l10n_latam_invoice_document', 'contacts',
                'account_tax_python', 'account_check_printing', 'account_followup', 'base_vat', 'mail', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'data/gt.county.csv',
        'data/res.country.state.csv',
        'data/gt.zone.csv',
        'data/l10n_latam.document.type.csv',
        'data/l10n_latam_identification_type_data.xml',
        'data/res_country_group_data.xml',
        'views/account_journal.xml',
        'views/ir_sequence_view.xml',
        'views/account_move_view.xml',
        'views/account_payment_view.xml',
        'views/res_currency_view.xml',
        'views/res_partner_view.xml',
        'views/res_config_settings_views.xml',
        'views/gt_county_views.xml',
        'views/res_company_views.xml',
        'views/sale_order_views.xml',
        'views/region_menu.xml',
        'views/account_tax_views.xml',
        'views/gt_zone_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
