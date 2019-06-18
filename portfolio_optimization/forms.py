from django import forms
from django.db.models.functions import Lower

from portfolio_optimization.models import EssDealTypeParameters


BADGE_SUCCESS_CLASS = 'badge badge-default badge-success'
FORM_CONTROL_CLASS = 'form-control input-lg'


class EssDealTypeParametersForm(forms.Form):
    """
    Form for Portfolio Optimization
    """
    deal_type_id = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'deal_type_id_to_edit'}), required=False)
    deal_type = forms.CharField(required=True, label="Deal Type", max_length=100,
                                widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                              'label_class': BADGE_SUCCESS_CLASS, 'id': 'deal_type',
                                                              'placeholder': 'Merger Arbitrage'}))
    long_probability = forms.FloatField(required=True, label="Long Probability",
                                        widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                      'label_class': BADGE_SUCCESS_CLASS,
                                                                      'id': 'long_probability','placeholder': '0.0'}))
    long_irr = forms.FloatField(required=True, label="Long Internal RoR",
                                widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                              'label_class': BADGE_SUCCESS_CLASS, 'id': 'long_irr',
                                                              'placeholder': '0.0'}))
    long_max_risk = forms.FloatField(required=True, label="Long Max Risk",
                                     widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                   'label_class': BADGE_SUCCESS_CLASS,
                                                                   'id': 'long_max_risk', 'placeholder': '0.0'}))
    long_max_size = forms.FloatField(required=True, label="Long Max Size",
                                     widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                   'label_class': BADGE_SUCCESS_CLASS,
                                                                   'id': 'long_max_size', 'placeholder': '0.0'}))
    short_probability = forms.FloatField(required=True, label="Short Probability",
                                         widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                       'label_class': BADGE_SUCCESS_CLASS,
                                                                       'id': 'short_probability', 'placeholder': '0.0'}))
    short_irr = forms.FloatField(required=True, label="Short Internal RoR",
                                 widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                               'label_class': BADGE_SUCCESS_CLASS, 'id': 'short_irr',
                                                               'placeholder': '0.0'}))
    short_max_risk = forms.FloatField(required=True, label="Short Internal RoR",
                                      widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                    'label_class': BADGE_SUCCESS_CLASS,
                                                                    'id': 'short_max_risk', 'placeholder': '0.0'}))
    short_max_size = forms.FloatField(required=True, label="Short Internal RoR",
                                      widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                    'label_class': BADGE_SUCCESS_CLASS,
                                                                    'id': 'short_max_size', 'placeholder': '0.0'}))

    def is_valid(self):
        """
        Validate the fields and display error message if not valid
        """
        valid = super(EssDealTypeParametersForm, self).is_valid()
        if not valid:
            return valid
        cleaned_data = self.cleaned_data
        deal_type_id = cleaned_data.get('deal_type_id')
        deal_type = cleaned_data.get('deal_type')
        deal_type_list = EssDealTypeParameters.objects.annotate(deal_type_lower=Lower('deal_type'))
        deal_type_list = list(deal_type_list.values_list('deal_type_lower', flat=True))
        if not deal_type_id and deal_type.lower() in deal_type_list:
            valid = False
            self._errors['deal_type'] = '{deal_type} already present. Kindly edit the existing one.'.format(deal_type=deal_type)

        return valid
