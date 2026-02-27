# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrderInherited(models.Model):
    _inherit = "sale.order"
    _name = "sale.order"

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrderInherited, self)._prepare_invoice()
        invoice_vals['invoice_doc_type'] = self.env.ref('l10n_gt_td_generic.dc_fact').id
        return invoice_vals
