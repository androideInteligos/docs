# -*- coding: utf-8 -*-

from num2words import num2words
from odoo.models import Model
from odoo import (fields, api, models, _, Command)


class AccountPaymentInherited(Model):
    _inherit = "account.payment"

    amount_in_words = fields.Char(compute='compute_amount_word', string='Monto en letras pagos')
    print_to_report = fields.Boolean(string="Mostrar en reporte", default=True)
    method = fields.Selection(
        [
            ("E", "Efectivo"),
            ("C", "Cheque"),
            ("T", "Transferencia"),
            ("TC", "Tarjeta de Credito"),
            ("DE", "Deposito"),
        ],
        string="Forma de Pago"
    )
    bank_reference = fields.Char(
        copy=False,
        help="Campo para ingresar referencia de banco en transferencias de pagos. "
             "Campo único, no pueden haber más de un registro con los mismos datos.",
        string="Referencia de banco"
    )

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

    @api.depends('amount')
    def compute_amount_word(self):
        """Método para manejar la conversión a letras de un monto de pago."""
        for record in self:
            amount = record.convert_amount_in_words(record.amount, 'es',
                                                    record.currency_id, record.partner_id.lang)
            record.amount_in_words = amount.capitalize()

    _sql_constraints = [
        ('bank_reference_unique', 'UNIQUE(bank_reference)', 'La referencia de banco ingresada ya existe!')
    ]

    def name_get(self):
        """Sobrescritura del método genérico para agregar número de cheque a nombre de pago"""
        names = []
        for record in self:
            check_number = str(record.check_number) if record.check_number else ''
            names.append(
                (record.id, '%s %s' % (record.name, '- ' + check_number))
            )
        return names
