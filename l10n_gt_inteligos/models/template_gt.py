
from odoo import models, _
from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = 'account.chart.template'

    @template('gt')
    def _get_gt_template_data(self):
        return {
            'name': _("Plantilla Contable Guatemala (Inteligos)"),
            # 'code_digits': '9', #Por defecto son 6, por lo que si es mayor se agregarán ceros a la derecha
            'property_account_receivable_id': 'cta_gt_110301',
            'property_account_payable_id': 'cta_gt_210106',
            'property_account_income_categ_id': 'cta_gt_410201',
            'property_account_expense_categ_id': 'cta_gt_510101',
        }

    @template('gt', 'res.company')
    def _get_gt_res_company(self):
        return {
            self.env.company.id: {
                'account_fiscal_country_id': 'base.gt',
                'bank_account_code_prefix': '10010',
                'cash_account_code_prefix': '10020',
                'transfer_account_code_prefix': '100301',
                'account_default_pos_receivable_account_id': 'cta_gt_110301', # Pendiente definir: Cuenta predeterminada para POS
                'income_currency_exchange_account_id': 'cta_gt_710203',
                'expense_currency_exchange_account_id': 'cta_gt_710203',
                'account_sale_tax_id': 'impuestos_plantilla_iva_por_pagar', # Pendiente definir: Impuesto de venta predeterminado
                'account_purchase_tax_id': 'impuestos_plantilla_iva_por_cobrar', # Pendiente definir: Impuesto de compra predeterminado

            },
        }

    @template(model='account.journal')
    def _get_account_journal(self, template_code):
        """ Override _get_account_journal method to add journals from Guatemala location"""
        return self._parse_csv(template_code, 'account.journal')

    @template(model='account.journal')
    def _get_latam_document_account_journal(self, template_code):
        """method override since Odoo default journals will not be used"""
        pass
