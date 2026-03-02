# -*- coding: utf-8 -*-

from datetime import timedelta
from num2words import num2words
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from odoo import (fields, api, models, _)
from odoo.exceptions import (UserError, AccessError)
from odoo.tools import (float_compare, format_date, get_lang, formatLang)


class AccountMoveInherited(models.Model):
    _inherit = "account.move"

    # ----------------------------------------------------------
    # l10n_gt_td_generic fields
    # ----------------------------------------------------------
    #  Campos para busqueda por NIT y Razon Social en Contabilidad, Ventas y CRM
    nit = fields.Char(string="NIT")
    legal_name = fields.Char(string="Razón Social")
    amount_in_words = fields.Char(compute='compute_amount_word', string='Monto en letras facturas')
    print_to_report = fields.Boolean(string="Mostrar en reporte", default=True)
    name = fields.Char(tracking=3)
    ref = fields.Char(tracking=3)
    date = fields.Date(
        string='Date',
        index=True,
        compute='_compute_date', store=True, required=True, readonly=False, precompute=True,
        copy=False,
        tracking=True,
    )
    journal_id = fields.Many2one(tracking=3)
    currency_id = fields.Many2one(tracking=3)
    state = fields.Selection(tracking=3)
    partner_id = fields.Many2one(tracking=3)
    credit_days = fields.Integer(store=True, compute='_compute_invoice_date', compute_sudo=False, string="Días crédito")
    invoice_doc_serie = fields.Char("Serie", copy=False)
    invoice_doc_number = fields.Char("Numero", copy=False)
    invoice_ref = fields.Char(string="Referencia", compute="_set_reference")

    # Necesario para Coversion segun tasa de cambio
    amount_total_signed_2 = fields.Monetary(string="Total segun Tasa de Cambio", readonly=True)
    rate_invoice = fields.Float(string='Tasa de Cambio', readonly=True, digits=(1, 12), compute='_compute_rate_invoice')
    inverse_rate_invoice = fields.Float(string='Tasa de Cambio Inversa',
                                        readonly=True, digits=(1, 6), compute='_compute_inverse_company_rate')

    # campo para calculo de fecha de pago segun configuracion de dias
    payment_date = fields.Char(
        compute='_compute_invoice_date', compute_sudo=False,
        help='Aquí va la fecha de la entrega del pago del pedido de compra, '
             'de formma estandar se traslada al siguiente viernes de la fecha de confirmacion de la compra.',
        string="Fecha Entrega de Pago",
        store=True,
    )

    # ----------------------------------------------------------
    # gt_territorial_division fields
    # ----------------------------------------------------------
    sub_region_id = fields.Many2one(
        comodel_name="gt.sub_region",
        related='partner_id.state_id.sub_region_id',
        depends=['partner_id.state_id',
                 'partner_id.state_id.sub_region_id'],
        store=True,
        string="Sub-región"
    )
    region_id = fields.Many2one(
        comodel_name="gt.region",
        related='partner_id.state_id.sub_region_id.region_id',
        depends=['partner_id.state_id',
                 'partner_id.state_id.sub_region_id',
                 'sub_region_id'],
        store=True,
        string="Región"
    )

    # ----------------------------------------------------------
    # l10n_gt_td_generic methods
    # ----------------------------------------------------------

    @api.depends('l10n_latam_available_document_type_ids')
    def _compute_l10n_latam_document_type(self):
        """
            Override to default the document configured in the sequence
            from the journal, if it is available in the document types
        """
        for rec in self.filtered(lambda x: x.state == 'draft' and (
                not x.posted_before if x.move_type in ['out_invoice', 'out_refund'] else True)):
            document_types = rec.l10n_latam_available_document_type_ids._origin
            sequence_document_type = rec.journal_id.sequence_id.l10n_latam_document_type_id \
                if rec.journal_id.sequence_id else False
            if sequence_document_type and sequence_document_type in document_types:
                if self.l10n_latam_document_type_id == self.env.ref('l10n_gt_inteligos.dc_fesp'):
                    pass
                else:
                    rec.l10n_latam_document_type_id = sequence_document_type
            else:
                rec.l10n_latam_document_type_id = (rec.company_id.l10n_latam_document_type_id
                                                   or document_types and document_types[0].id)

    def _is_manual_document_number(self):
        """  Avoid manually entering the document number on the supplier invoice """
        return False

    @api.model
    def convert_amount_in_words(self, amount, language, currency, lang):
        """
        Método para convertir un valor numérico en letras.
        :param amount: int or float value
        :param language: str value to language response
        :param currency: account.currency object
        :param lang: str value to localization
        :return: str amount in words
        """
        list_lang = [['en', 'en_US'], ['en', 'en_AU'], ['en', 'en_GB'], ['en', 'en_IN'],
                     ['fr', 'fr_BE'], ['fr', 'fr_CA'], ['fr', 'fr_CH'], ['fr', 'fr_FR'],
                     ['es', 'es_ES'], ['es', 'es_AR'], ['es', 'es_BO'], ['es', 'es_CL'], ['es', 'es_CO'],
                     ['es', 'es_CR'], ['es', 'es_DO'],
                     ['es', 'es_EC'], ['es', 'es_GT'], ['es', 'es_MX'], ['es', 'es_PA'], ['es', 'es_PE'],
                     ['es', 'es_PY'], ['es', 'es_UY'], ['es', 'es_VE'],
                     ['lt', 'lt_LT'], ['lv', 'lv_LV'], ['no', 'nb_NO'], ['pl', 'pl_PL'], ['ru', 'ru_RU'],
                     ['dk', 'da_DK'], ['pt_BR', 'pt_BR'], ['de', 'de_DE'], ['de', 'de_CH'],
                     ['ar', 'ar_SY'], ['it', 'it_IT'], ['he', 'he_IL'], ['id', 'id_ID'], ['tr', 'tr_TR'],
                     ['nl', 'nl_NL'], ['nl', 'nl_BE'], ['uk', 'uk_UA'], ['sl', 'sl_SI'], ['vi_VN', 'vi_VN']]

        #     ['th','th_TH'],['cz','cs_CZ']
        cnt = 0
        for rec in list_lang[cnt:len(list_lang)]:
            if rec[1] == lang:
                language = rec[0]
            cnt += 1

        amount_str = str('{:2f}'.format(amount))
        amount_str_splt = amount_str.split('.')
        before_point_value = amount_str_splt[0]
        after_point_value = amount_str_splt[1][:2]

        before_amount_words = num2words(int(before_point_value), lang=language)
        after_amount_words = num2words(int(after_point_value), lang=language)

        amount = before_amount_words

        if currency and currency.currency_unit_label:
            amount += ' ' + currency.currency_unit_label

        if currency and currency.amount_separator:
            amount += ' ' + currency.amount_separator

        if int(after_point_value) > 0:
            amount += ' con ' + str(after_point_value) + '/100.'
        else:
            amount += ' exactos.'

        return amount

    @api.depends('amount_total')
    def compute_amount_word(self):
        """Método para manejar la conversión a letras de un monto de pago."""
        for record in self:
            amount = record.convert_amount_in_words(record.amount_total, 'es',
                                                    record.currency_id, record.partner_id.lang)
            record.amount_in_words = amount.capitalize()

    # campo para calculo de fecha de pago segun configuracion de dias
    @api.depends('invoice_date', 'invoice_date_due')
    def _compute_invoice_date(self):
        """
        Actualización del 21.05.2021
        Mejora a código de computación de los campos:
            credit_days
            payment_date
        Reducción de código y mejora en la legibilidad del mismo.
        Aparte solución a fallo al no ingresar una fecha de factura de forma manual,
        ya que esto impedia calcular los dias credito y la fecha de pago.
        :return:
        """
        for record in self:
            # changegt
            if record.country_code == 'GT':
                day = record.invoice_date or fields.Date.today()
                record.credit_days = (record.invoice_date_due - day).days if record.invoice_date_due else 0
                payment_day = record.env.company.payment_day or 4
                if payment_day - day.weekday() <= 0:
                    date = day - timedelta(days=day.weekday()) + timedelta(days=payment_day, weeks=1)
                else:
                    date = day - timedelta(days=day.weekday()) + timedelta(days=payment_day)
                record.payment_date = date.strftime("%d/%m/%Y")
            else:
                record.credit_days = 0
                record.payment_date = False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        Herencia del método propio de Odoo para agregar lógica que permita obtener desde los documentos
        fiscales y contables el valor de nit y razón social del contacto seleccionado.
        :return: None o alerta del tipo 'warning'
        """
        result = super(AccountMoveInherited, self)._onchange_partner_id()
        # changegt
        if self.country_code == 'GT':

            if self.state == 'draft' and self.partner_id:
                self.write({'nit': self.partner_id.vat, 'legal_name': self.partner_id.legal_name})

        return result

    @api.depends('invoice_date', 'company_id')
    def _compute_date(self):
        """Sobrescritura del método genérico para modificar el funcionamiento de asignación
                    de una fecha contable sólo cuando los tipos de
                    documentos son:
                    * Z1. ('out_invoice', 'out_refund', 'out_receipt'),
                    ya que en este caso deben ser valores iguales los de los campos
                    ´invoice_date´, fecha de factura, y ´date´, fecha contable,.
                    * Z2. Si los documentos son de tipo de proveedor,
                    las fechas contables y fecha de las facturas pueden ser distintas,
                    máximo mayores a 2 meses con respecto a la fecha de la factura.
                    * A1. Tener en cuenta que en Odoo15, el funcionamiento normal
                    es que la fecha contable siempre depende de la fecha de la factura.
                    Por tanto, para obtener o actualizar la fecha contable según los lineamientos anteriores (Z1 Y Z2),
                    se hará conforme a lo anterior indicado (A1).
                    Se agrga validación, donde, si es un apunte contable ('entry'),
                    conservará la fecha de factura como fecha contable.
                """
        # changegt
        if self.env.company.account_fiscal_country_id.code == 'GT':

            for move in self:
                if not move.invoice_date:
                    if not move.date:
                        move.date = fields.Date.context_today(self)
                    continue
                accounting_date = move.invoice_date
                if not move.is_sale_document(include_receipts=True):
                    accounting_date = move._get_accounting_date(move.invoice_date, move._affect_tax_report())

                delta = relativedelta(move.date, move.invoice_date)
                res_months = delta.months + (delta.years * 12)

                if accounting_date and accounting_date != move.date:
                    if move.move_type == 'entry':
                        move.date = move.invoice_date if move.invoice_date else accounting_date
                    else:
                        move.date = accounting_date
                    # _affect_tax_report may trigger premature recompute of line_ids.date
                    self.env.add_to_compute(move.line_ids._fields['date'], move.line_ids)
                    # might be protected because `_get_accounting_date` requires the `name`
                    self.env.add_to_compute(self._fields['name'], move)
                elif (move.move_type in ('in_invoice', 'in_refund') and (res_months < 0 or res_months > 2)
                      and (str(move.l10n_latam_document_type_id.doc_code_prefix).strip() != "RECI")):
                    raise UserError('Sólo es posible tener una diferencia '
                                    'de 2 meses entre la fecha contable y la fecha de la factura.'
                                    'La fecha de la factura núnca puede ser mayor a la fecha contable.')
        else:
            super()._compute_date()

    def action_post(self):
        """Sobrescritura del método para asignar una fecha de documento según haya o no valores en los campos
            ´invoice_date´ y ´date´. Si no hay valores en dichos campos, colocar la fecha de hoy, en otro caso,
            colocar el valor del campo ´date´ o ´invoice_date´ en ese orden.
        """
        # changegt
        if self.country_code == 'GT':
            self.invoice_date = fields.Date.context_today(self) \
                if not self.invoice_date and not self.date else self.invoice_date or self.date
            self._compute_date()
        return super(AccountMoveInherited, self).action_post()

    @api.model
    @api.depends('currency_id')
    def _compute_rate_invoice(self):
        for record in self:
            # changegt
            if record.country_code == 'GT':

                rate_invoice = [r['company_rate'] for r in record['currency_id']['rate_ids']
                                if record['invoice_date'] == r['name']]
                if rate_invoice:
                    record.rate_invoice = rate_invoice[0]
                elif record['company_id']['currency_id']['rate_ids']:
                    rate_invoice = [r['company_rate'] for r in record['company_id']['currency_id']['rate_ids']
                                    if record['invoice_date'] == r['name']]
                    if rate_invoice:
                        record.rate_invoice = rate_invoice[0]
                    else:
                        record.rate_invoice = record['company_id']['currency_id']['rate']
                else:
                    record.rate_invoice = record['currency_id']['rate']
            else:
                record.rate_invoice = 0.0

    # Necesario para Coversion segun tasa de cambio

    @api.model
    @api.depends('currency_id')
    def _compute_inverse_company_rate(self):
        for record in self:
            # changegt
            if record.country_code == 'GT':

                inverse_rate_invoice = [r['inverse_company_rate'] for r in record['currency_id']['rate_ids']
                                        if record['invoice_date'] == r['name']]
                if inverse_rate_invoice:
                    record.inverse_rate_invoice = inverse_rate_invoice[0]
                elif record['company_id']['currency_id']['rate_ids']:
                    inverse_rate_invoice = [r['inverse_company_rate'] for r in
                                            record['company_id']['currency_id']['rate_ids']
                                            if record['invoice_date'] == r['name']]
                    if inverse_rate_invoice:
                        record.inverse_rate_invoice = inverse_rate_invoice[0]
                    else:
                        record.inverse_rate_invoice = record['company_id']['currency_id']['inverse_rate']
                else:
                    record.inverse_rate_invoice = record['currency_id']['inverse_rate']
            else:
                record.inverse_rate_invoice = 0.0

    def _set_reference(self):
        for rec in self:
            # changegt
            if rec.country_code == 'GT':

                if rec.invoice_doc_serie:
                    rec.invoice_ref = '%s %s-%s' % (
                        rec.l10n_latam_document_type_id.name, rec.invoice_doc_serie, rec.invoice_doc_number)

                else:
                    rec.invoice_ref = '%s %s' % (rec.l10n_latam_document_type_id.name, rec.invoice_doc_number)
            else:
                rec.invoice_ref = False

    def _get_sequence(self):
        """ Return the sequence to be used during the post of the current move.
            :return: An ir.sequence record or False.
        """
        self.ensure_one()

        journal = self.journal_id
        if self.move_type in (
                'entry', 'out_invoice', 'in_invoice', 'out_receipt', 'in_receipt') or not journal.refund_sequence:
            return journal.sequence_id
        if not journal.refund_sequence_id:
            return
        return journal.refund_sequence_id

    def set_values_by_sequence(self, sequence):
        """
        Método para obtener y asignar los datos desde la secuencia activa según el diario enlazado a ´self´.
        :param sequence: registro del tipo ir.sequence que hace referencia a la secuencia del diario enlazado a ´self´.
        :return: None
        """
        if self.move_type in ['out_invoice', 'out_refund'] or sequence.l10n_latam_document_type_id == self.env.ref(
                'l10n_gt_inteligos.dc_fesp'):
            to_write = {
                'l10n_latam_document_type_id': sequence.l10n_latam_document_type_id,
                'invoice_doc_serie': sequence._get_prefix_suffix(date=self.invoice_date or fields.Date.today(),
                                                                 date_range=self.invoice_date)[0],
                'invoice_doc_number': '%%0%sd' % sequence.padding % sequence._get_current_sequence().number_next_actual,
                'name': sequence.next_by_id(sequence_date=self.date)
            }
            self.write(to_write)

    def _post(self, soft=True):
        """Post/Validate the documents.

        Posting the documents will give it a number, and check that the document is
        complete (some fields might not be required if not posted but are required
        otherwise).
        If the journal is locked with a hash table, it will be impossible to change
        some fields afterwards.

        :param soft (bool): if True, future documents are not immediately posted,
            but are set to be auto posted automatically at the set accounting date.
            Nothing will be performed on those documents before the accounting date.
        :return Model<account.move>: the documents that have been posted
        """
        if self.env.company.account_fiscal_country_id.code == 'GT':

            if not self.env.su and not self.env.user.has_group('account.group_account_invoice'):
                raise AccessError(_("You don't have the access rights to post an invoice."))

            # Avoid marking is_manually_modified as True when posting an invoice
            self = self.with_context(skip_is_manually_modified=True)  # noqa: PLW0642

            validation_msgs = set()

            for invoice in self.filtered(lambda move: move.is_invoice(include_receipts=True)):
                if (
                    invoice.quick_edit_mode
                    and invoice.quick_edit_total_amount
                    and invoice.currency_id.compare_amounts(invoice.quick_edit_total_amount, invoice.amount_total) != 0
                ):
                    validation_msgs.add(_(
                        "The current total is %(current_total)s but the expected total is %(expected_total)s. In order to post the invoice/bill, "
                        "you can adjust its lines or the expected Total (tax inc.).",
                        current_total=formatLang(self.env, invoice.amount_total, currency_obj=invoice.currency_id),
                        expected_total=formatLang(self.env, invoice.quick_edit_total_amount, currency_obj=invoice.currency_id),
                    ))
                if invoice.partner_bank_id and not invoice.partner_bank_id.active:
                    validation_msgs.add(_(
                        "The recipient bank account linked to this invoice is archived.\n"
                        "So you cannot confirm the invoice."
                    ))
                if float_compare(invoice.amount_total, 0.0, precision_rounding=invoice.currency_id.rounding) < 0:
                    validation_msgs.add(_(
                        "You cannot validate an invoice with a negative total amount. "
                        "You should create a credit note instead. "
                        "Use the action menu to transform it into a credit note or refund."
                    ))

                if not invoice.partner_id:
                    if invoice.is_sale_document():
                        validation_msgs.add(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
                    elif invoice.is_purchase_document():
                        validation_msgs.add(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

                # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
                # lines are recomputed accordingly.
                if not invoice.invoice_date:
                    if invoice.is_sale_document(include_receipts=True):
                        invoice.invoice_date = fields.Date.context_today(self)
                    elif invoice.is_purchase_document(include_receipts=True):
                        validation_msgs.add(_("The Bill/Refund date is required to validate this document."))

            for move in self:
                if move.state in ['posted', 'cancel']:
                    validation_msgs.add(_('The entry %(name)s (id %(id)s) must be in draft.', name=move.name, id=move.id))
                if not move.line_ids.filtered(lambda line: line.display_type not in ('line_section', 'line_note')):
                    validation_msgs.add(_('You need to add a line before posting.'))
                if not soft and move.auto_post != 'no' and move.date > fields.Date.context_today(self):
                    date_msg = move.date.strftime(get_lang(self.env).date_format)
                    validation_msgs.add(_("This move is configured to be auto-posted on %(date)s", date=date_msg))
                if not move.journal_id.active:
                    validation_msgs.add(_(
                        "You cannot post an entry in an archived journal (%(journal)s)",
                        journal=move.journal_id.display_name,
                    ))
                if move.display_inactive_currency_warning:
                    validation_msgs.add(_(
                        "You cannot validate a document with an inactive currency: %s",
                        move.currency_id.name
                    ))

                if move.line_ids.account_id.filtered(lambda account: account.deprecated) and not self._context.get('skip_account_deprecation_check'):
                    validation_msgs.add(_("A line of this move is using a deprecated account, you cannot post it."))

                # If the field autocheck_on_post is set, we want the checked field on the move to be checked
                move.checked = move.journal_id.autocheck_on_post

            if validation_msgs:
                msg = "\n".join([line for line in validation_msgs])
                raise UserError(msg)

            if soft:
                future_moves = self.filtered(lambda move: move.date > fields.Date.context_today(self))
                for move in future_moves:
                    if move.auto_post == 'no':
                        move.auto_post = 'at_date'
                    msg = _('This move will be posted at the accounting date: %(date)s', date=format_date(self.env, move.date))
                    move.message_post(body=msg)
                to_post = self - future_moves
            else:
                to_post = self

            for move in to_post:
                affects_tax_report = move._affect_tax_report()
                lock_dates = move._get_violated_lock_dates(move.date, affects_tax_report)
                if lock_dates:
                    move.date = move._get_accounting_date(move.invoice_date or move.date, affects_tax_report, lock_dates=lock_dates)

            # Create the analytic lines in batch is faster as it leads to less cache invalidation.
            to_post.line_ids._create_analytic_lines()

            # Trigger copying for recurring invoices
            to_post.filtered(lambda m: m.auto_post not in ('no', 'at_date'))._copy_recurring_entries()

            for invoice in to_post:
                # Fix inconsistencies that may occure if the OCR has been editing the invoice at the same time of a user. We force the
                # partner on the lines to be the same as the one on the move, because that's the only one the user can see/edit.
                wrong_lines = invoice.is_invoice() and invoice.line_ids.filtered(lambda aml:
                    aml.partner_id != invoice.commercial_partner_id
                    and aml.display_type not in ('line_note', 'line_section')
                )
                if wrong_lines:
                    wrong_lines.write({'partner_id': invoice.commercial_partner_id.id})

            # reconcile if state is in draft and move has reversal_entry_id set
            draft_reverse_moves = to_post.filtered(lambda move: move.reversed_entry_id and move.reversed_entry_id.state == 'posted')

            to_post.write({
                'state': 'posted',
                'posted_before': True,
            })

            draft_reverse_moves.reversed_entry_id._reconcile_reversed_moves(draft_reverse_moves, self._context.get('move_reverse_cancel', False))
            to_post.line_ids._reconcile_marked()

            for invoice in to_post:
                partner_id = invoice.partner_id
                subscribers = [partner_id.id] if partner_id and partner_id not in invoice.sudo().message_partner_ids else None
                invoice.message_subscribe(subscribers)

                """Adición Inteligos al método genérico, cambiar esta sección durante la migración entre
                                versiones de Odoo"""
                # Get the journal's sequence.
                sequence = move._get_sequence()
                if not sequence:
                    raise UserError(_('Please define a sequence on your journal.'))
                move.set_values_by_sequence(sequence)
                """Fin Adición Inteligos al método genérico"""

            customer_count, supplier_count = defaultdict(int), defaultdict(int)
            for invoice in to_post:
                if invoice.is_sale_document():
                    customer_count[invoice.partner_id] += 1
                elif invoice.is_purchase_document():
                    supplier_count[invoice.partner_id] += 1
                elif invoice.move_type == 'entry':
                    sale_amls = invoice.line_ids.filtered(lambda line: line.partner_id and line.account_id.account_type == 'asset_receivable')
                    for partner in sale_amls.mapped('partner_id'):
                        customer_count[partner] += 1
                    purchase_amls = invoice.line_ids.filtered(lambda line: line.partner_id and line.account_id.account_type == 'liability_payable')
                    for partner in purchase_amls.mapped('partner_id'):
                        supplier_count[partner] += 1
            for partner, count in customer_count.items():
                (partner | partner.commercial_partner_id)._increase_rank('customer_rank', count)
            for partner, count in supplier_count.items():
                (partner | partner.commercial_partner_id)._increase_rank('supplier_rank', count)

            # Trigger action for paid invoices if amount is zero
            to_post.filtered(
                lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
            )._invoice_paid_hook()

            return to_post
        else:
            return super()._post(soft)

    @api.constrains('invoice_doc_serie', 'invoice_doc_number')
    def _check_duplicate_supplier_reference(self):
        for invoice in self:
            # refuse to validate a vendor bill/credit note if there already exists one with the same reference for
            # the same partner, because it's probably a double encoding of the same bill/credit note only if the two
            # invoices are validated.
            # changegt
            if invoice.country_code == 'GT':
                self.ensure_one()
                if invoice.move_type in (
                        'in_invoice', 'in_refund') and invoice.invoice_doc_number and invoice.invoice_doc_serie:
                    res = self.env['account.move'].search([
                        ('move_type', '=', invoice.move_type),
                        ('invoice_doc_serie', '=', invoice.invoice_doc_serie),
                        ('invoice_doc_number', '=', invoice.invoice_doc_number),
                        ('company_id', '=', invoice.company_id.id),
                        ('partner_id', '=', invoice.partner_id.id),
                        ('l10n_latam_document_type_id', '=', invoice.l10n_latam_document_type_id.id),
                        ('id', '!=', invoice.id),
                        ('state', 'in', ('draft', 'posted'))])
                    if res:
                        raise UserError(
                            "Se ha detectado una referencia duplicada para la factura de proveedor. "
                            "Es probable que tengas más de un documento con los mismos datos.")

    def button_cancel(self):
        """Sobrescritura del método para agregar restricción según el campo ´date´, fecha contable.
            Si entre la fecha de hoy y la fecha contable no hay una diferencia mayor o igual a 2 meses,
            o bien, si el usuario pertenece al grupo administrativo de contabilidad se podrá anular los documentos.
        """
        # changegt
        if self.country_code == 'GT':

            delta = relativedelta(fields.Date.context_today(self), self.date)
            res_months = delta.months + (delta.years * 12)

            if res_months >= 2 and not self.env.user.has_group('account.group_account_manager'):
                raise UserError('No es posible anular un documento después de 2 meses de su publicación.')

        super(AccountMoveInherited, self).button_cancel()
