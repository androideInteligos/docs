# -*- coding: utf-8 -*-

from odoo import models


class SaleAdvancePaymentInvInherited(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _prepare_invoice_values(self, order, so_line):
        res = super()._prepare_invoice_values(order, so_line)
        res['invoice_doc_type'] = self.env.ref('l10n_gt_td_generic.dc_fact').id
        return res
