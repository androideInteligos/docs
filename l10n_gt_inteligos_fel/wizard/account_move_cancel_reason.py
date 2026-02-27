# -*- coding: utf-8 -*-

from odoo.models import TransientModel
from odoo.fields import (Many2one, Selection, Char)


class AccountMoveCancelReason(TransientModel):
    _name = "account.move.cancel_reason"
    _description = "Interfaz de usuario para ingresar una razón de anulación de DTEs"

    move_id = Many2one(comodel_name="account.move", string="Doc. Fiscal")
    move_type = Selection(related="move_id.move_type", string="Tipo de movimiento")
    reason_note = Char(related="move_id.reason_note", readonly=False, string="Razón")

    def button_cancel(self):
        """
        Método útil para manejar la anulación con un mensaje o razón.
        :return:
        """
        self.move_id.with_context(
            default_move_type=self.move_id.move_type, default_invoice_doc_type=self.move_id.invoice_doc_type.id
        ).button_cancel()
