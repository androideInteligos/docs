from odoo import models, fields, api


class AccountJournalInherited(models.Model):
    """"Extensión del modelo account.journal para agregarle la lógica de secuencias"""
    _inherit = "account.journal"

    sequence_id = fields.Many2one(
        'ir.sequence', string='Secuencia principal',
        help="This field contains the information related to the numbering of the journal "
             "entries of this journal.",
        copy=False
    )
    refund_sequence_id = fields.Many2one(
        'ir.sequence', string='Secuencia NCRE',
        help="This field contains the information related to the numbering of the "
             "credit note entries of this journal.",
        copy=False
    )

    @api.model
    def _create_sequence(self, vals, refund=False):
        """Actualización del 29.10.2021
            Creación de la función en Odoo 14 para la creación de secuencias en los diarios contables,
            ya que Odoo 14 eliminó esto en comparación con v13.
            Hacer uso de varios tipos de documentos en un mismo diario es posible debido a la mejora.
        """
        seq_name = refund and vals.get('code', '') + ': Rectificativa' or vals.get('code', '')
        seq = {
            'name': '%s Secuencia' % seq_name,
            'implementation': 'no_gap',
            'prefix': '',
            'padding': 4,
            'number_increment': 1,
            'use_date_range': False,
            'journal_id': vals.get('id', False),
            'l10n_latam_document_type_id': vals.get('doc_type_id', False) or self.env.ref(
                'l10n_gt_inteligos.dc_fact').id
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        seq = self.env['ir.sequence'].create(seq)

        return seq

    @api.model_create_multi
    def create(self, vals_list):
        """Actualización del 29.10.2021
            Sobreescritura del método genérico create del los diarios contables
            para agregar lógica de creación de secuencias para las facturas y las notas de crédito
            ya que Odoo 14 eliminó esto en comparación con v13.
            Hacer uso de varios tipos de documentos en un mismo diario es posible debido a la mejora.
        """
        # changegt
        if self.env.company.account_fiscal_country_id.code == 'GT':
            for vals in vals_list:
                if not vals.get('sequence_id'):
                    vals.update({'sequence_id': self.sudo()._create_sequence(vals).id})
                if vals.get('type') == 'sale' and vals.get('refund_sequence') and not vals.get('refund_sequence_id'):
                    vals.update({'refund_sequence_id': self.sudo()._create_sequence(vals, refund=True).id})
        journal = super(AccountJournalInherited, self.with_context(mail_create_nolog=True)).create(vals_list)

        return journal

    def write(self, vals):
        """Actualización del 29.10.2021
            Sobreescritura del método genérico write del los diarios contables
            para agregar lógica de creación de secuencias para las facturas y las notas de crédito
            ya que Odoo 14 eliminó esto en comparación con v13.
            Hacer uso de varios tipos de documentos en un mismo diario es posible debido a la mejora.
        """
        result = super(AccountJournalInherited, self).write(vals)
        # changegt
        if self.country_code == 'GT':

            if not self.sequence_id:
                vals.update({'sequence_id': self.sudo()._create_sequence(vals).id})

            if vals.get('refund_sequence'):
                for journal in self.filtered(lambda j: j.type == 'sale' and not j.refund_sequence_id):
                    journal_vals = {
                        'name': journal.name,
                        'company_id': journal.company_id.id,
                        'code': journal.code,
                        'id': journal.id,
                        'doc_type_id': self.env.ref('l10n_gt_inteligos.dc_ncre').id
                    }
                    journal.refund_sequence_id = self.sudo()._create_sequence(journal_vals, refund=True).id

        return result
