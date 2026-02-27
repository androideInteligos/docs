# -*- coding: utf-8 -*-
{
    'name': "Emisiones FEL Guatemala",
    'summary': """
        Implementación FEL en Odoo por Inteligos""",
    'description': """
        Este módulo permite la facturación FEL de Guatemala para distintos proveedores. 
        Los actualmente integrados son: INFILE, MegaPrint, Digifact, eForcon, Ecofacturas, Contap
    """,
    'author': "Proyectos Agiles, S.A. - Inteligos",
    'website': "https://www.inteligos.gt",
    'category': 'Accounting',
    'version': '16.0.1.5',
    "license": "LGPL-3",
    'depends': ['base', 'account', 'l10n_gt_td_generic', 'gt_territorial_division', 'web_notify'],
    'data': [
        'data/uom_uom.xml',
        'data/l10n_latam_identification_type_data.xml',
        'data/fel_phrases.xml',
        'data/server_action_massive_fel.xml',
        'data/mail_template_data.xml',
        'security/inteligos_fel_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/account_move_view.xml',
        'views/account_journal.xml',
        'views/res_config_settings_account_views.xml',
        'wizard/custom_reason_cancel_move.xml',
        'reports/report_invoice_document_inteligos.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False
}
