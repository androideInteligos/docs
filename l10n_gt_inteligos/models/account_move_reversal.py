# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMoveReversalInherited(models.TransientModel):
    _inherit = "account.move.reversal"

    @api.depends('l10n_latam_available_document_type_ids', 'journal_id')
    def _compute_document_type(self):
        """
            Override to default the document configured in the sequence
            from the journal, if it is available in the document types
        """
        for record in self.filtered(
                lambda x: not x.l10n_latam_document_type_id or
                          x.l10n_latam_document_type_id not in x.l10n_latam_available_document_type_ids):
            document_types = record.l10n_latam_available_document_type_ids._origin
            sequence_document_type = record.journal_id.sequence_id.l10n_latam_document_type_id \
                if record.journal_id.sequence_id else False
            if sequence_document_type and sequence_document_type in document_types:
                record.l10n_latam_document_type_id = sequence_document_type
            else:
                record.l10n_latam_document_type_id = document_types[0] if document_types else False
