# -*- coding: utf-8 -*-

import re
from odoo.models import AbstractModel


class SequenceMixin(AbstractModel):
    _inherit = 'sequence.mixin'

    def _get_sequence_format_param(self, previous):
        """ Sobrescritura de método. """
        sequence_number_reset = self._deduce_sequence_number_reset(previous)
        regex = self._sequence_fixed_regex

        if sequence_number_reset == 'year':
            regex = self._sequence_yearly_regex
        elif sequence_number_reset == 'year_range':
            regex = self._sequence_year_range_regex
        elif sequence_number_reset == 'month':
            regex = self._sequence_monthly_regex

        format_values = re.match(regex, previous).groupdict()
        format_values['seq_length'] = len(format_values['seq'])
        format_values['year_length'] = len(format_values.get('year') or '')
        format_values['year_end_length'] = len(format_values.get('year_end') or '')

        if not format_values.get('seq') and 'prefix1' in format_values and 'suffix' in format_values:
            # if we don't have a seq, consider we only have a prefix and not a suffix
            format_values['prefix1'] = format_values['suffix']
            format_values['suffix'] = ''

        format_values['prefix1'] = f'{self.journal_id.code}/'

        for field in ('seq', 'year', 'month', 'year_end'):
            format_values[field] = int(format_values.get(field) or 0)

        placeholders = re.findall(r'\b(prefix\d|seq|suffix\d?|year|year_end|month)\b', regex)
        format = ''.join(
            "{seq:0{seq_length}d}" if s == 'seq' else
            "{month:02d}" if s == 'month' else
            "{year:0{year_length}d}" if s == 'year' else
            "{year_end:0{year_end_length}d}" if s == 'year_end' else
            "{%s}" % s
            for s in placeholders
        )
        return format, format_values
