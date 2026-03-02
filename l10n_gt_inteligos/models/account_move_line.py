# -*- coding: utf-8 -*-

from odoo import (fields, api, models)


class AccountInvoiceLine(models.Model):
    _inherit = "account.move.line"

    line_total = fields.Monetary(string='Importe', store=True, readonly=True, compute='_compute_price')
    price_subtotal_signed_2 = fields.Monetary(string="Subtotal segun Tasa de Cambio", readonly=True)

    @api.depends('price_unit', 'discount', 'quantity', 'product_id', 'move_id.partner_id', 'move_id.currency_id',
                 'move_id.company_id', 'move_id.invoice_date', 'move_id.date')
    def _compute_price(self):
        for rec in self:
            price = rec.price_unit * (1 - (rec.discount or 0.0) / 100.0)
            rec.line_total = price * rec.quantity
