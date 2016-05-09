import re

from pygments.lexers import get_all_lexers
from django import forms
from django.utils.html import mark_safe

from djblets.extensions.forms import SettingsForm


def _all_names():
    return [lexer[1][0] for lexer in get_all_lexers()]


def _all_aliases():
    return set([alias for lexer in get_all_lexers() for alias in lexer[1]])


class PygmentsOverrideSettingsForm(SettingsForm):
    overrides = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': '.config=ini\n.tt=json'}),
        required=False,
        help_text=
        u'Use a list of .ext=type pairs, one per line. I.e: .tt=json ' +
        'The complete list of available lexers is: %s.' % ', '.join(sorted(
            _all_names())))

    def clean_overrides(self):
        overrides = self.normalize_overrides(self.cleaned_data['overrides'])
        # The regexp stands for a list of break-line ended .ext=type pairs.
        if not re.match('^(\.\w+=[\w\+\-]+\n)*$', overrides):
            raise forms.ValidationError(
                u'Incorrect override format. Use .ext=type, one per line.')

        if overrides:
            lexer_names = set(re.findall('([\w\+\-]+)\n', overrides))
            invalid_names = [name
                             for name in lexer_names
                             if name not in _all_aliases()]
            if invalid_names:
                raise forms.ValidationError(mark_safe(
                    u'The following names for syntax highlighting do not exist. '
                    + 'Please, check the spelling carefully:<br/>%s' %
                    self.format_unrecognized_names(invalid_names)))

        return overrides

    def normalize_overrides(self, raw_overrides):
        lines = raw_overrides.strip().splitlines()
        break_line_delimited_pairs = [line.strip() + '\n' for line in lines]
        return ''.join(break_line_delimited_pairs)

    def format_unrecognized_names(self, names):
        def suggestion(name):
            import difflib
            sug = difflib.get_close_matches(name, _all_aliases(), cutoff=0.4)
            if len(sug) == 0:
                return u''
            elif len(sug) == 1:
                return u'(perhaps you meant %s)' % sug[0]
            else:
                return u'(perhaps you meant one of %s)' % ', '.join(sug)

        return '<br/>'.join(['%s %s' % (name, suggestion(name)) for name in
                             names])
