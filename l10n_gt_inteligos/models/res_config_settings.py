
from odoo import fields, models


class ResConfigAccount(models.TransientModel):
    _inherit = "res.config.settings"

    duplicate_nit = fields.Boolean(
        store=True,
        index=True,
        related="company_id.duplicate_nit",
        readonly=False,
        string="¿Existiran NITs duplicados?",
    )
    payment_day = fields.Integer(
        store=True,
        index=True,
        related="company_id.payment_day",
        readonly=False,
        string="Día de pago",
    )
    l10n_latam_document_type_id = fields.Many2one(
        comodel_name='l10n_latam.document.type',
        related="company_id.l10n_latam_document_type_id", readonly=False,
        string='Tipo Documento predeterminado', copy=False
    )
