from datetime import date

from django import forms
from django.conf import settings
from django_slack import slack_message

from risk.models import MA_Deals
from risk_reporting.models import FormulaeBasedDownsides
from slack_utils import get_channel_name


BADGE_SUCCESS_CLASS = 'badge badge-default badge-success'
BADGE_DARK_CLASS = 'badge badge-default badge-dark'
DATE_PICKER_CLASS = 'form-control'
CUSTOM_SELECT_CLASS = 'custom-select form-control input-lg'
FORM_CONTROL_CLASS = 'form-control input-lg'
MAX_ACTUAL_DATE = date.today().strftime('%Y-%m-%d')

POSITION_ACQUIRER_CHOICES = [
    ('no', 'No'),
    ('yes', 'Yes')
]

class CreateMaDealsForm(forms.Form):
    """
    Form for adding new M&A Deal
    """
    deal_name = forms.CharField(required=True, label="Deal Name", max_length=100,
                                widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                              'label_class': BADGE_SUCCESS_CLASS, 'id': 'deal_name',
                                                              'placeholder': 'IBM - RHT'}))
    analyst = forms.CharField(required=True, label="Analyst", max_length=50,
                              widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                            'label_class': BADGE_SUCCESS_CLASS, 'id': 'analyst',
                                                            'placeholder': 'John Doe'}))
    target_ticker = forms.CharField(required=True, label="Target Ticker", max_length=50,
                                    widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                  'label_class': BADGE_DARK_CLASS, 'id': 'target_ticker',
                                                                  'placeholder': 'AAPL US EQUITY'}))
    acquirer_ticker = forms.CharField(required=False, label="Acquirer Ticker", max_length=50,
                                      widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                    'label_class': BADGE_DARK_CLASS,
                                                                    'id': 'acquirer_ticker', 'placeholder': 'GOOGL US EQUITY'}))
    deal_cash_terms = forms.FloatField(required=False, label="Deal Cash Terms",
                                       widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                     'label_class': BADGE_DARK_CLASS,
                                                                     'id': 'deal_cash_terms', 'placeholder': '0.00'}))
    deal_share_terms = forms.FloatField(required=False, label="Deal Share Terms",
                                        widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                      'label_class': BADGE_DARK_CLASS,
                                                                      'id': 'deal_share_terms', 'placeholder': '0.00'}))
    deal_value = forms.FloatField(required=True, label="Deal Value",
                                  widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                'label_class': BADGE_SUCCESS_CLASS,
                                                                'id': 'deal_value', 'placeholder': '000.00'}))
    expected_close_date = forms.DateField(required=True, label="Expected Close Date",
                                          widget=forms.TextInput(attrs={'type': 'date', 'class':DATE_PICKER_CLASS,
                                                                        'label_class': BADGE_DARK_CLASS,
                                                                        'id': 'expected_close_date'}))
    target_dividends = forms.FloatField(required=False, label="Target Dividends",
                                        widget=forms.TextInput(attrs={'class': CUSTOM_SELECT_CLASS,
                                                                      'label_class': BADGE_SUCCESS_CLASS,
                                                                      'id': 'target_dividends', 'placeholder': '0.00'}))
    acquirer_dividends = forms.FloatField(required=False, label="Acquirer Dividends",
                                          widget=forms.TextInput(attrs={'class': CUSTOM_SELECT_CLASS,
                                                                        'label_class': BADGE_SUCCESS_CLASS,
                                                                        'id': 'acquirer_dividends',
                                                                        'placeholder': '0.00'}))
    short_rebate = forms.FloatField(required=False, label="Short Rebate",
                                    widget=forms.TextInput(attrs={'class': CUSTOM_SELECT_CLASS,
                                                                  'label_class': BADGE_SUCCESS_CLASS,
                                                                  'id': 'short_rebate', 'placeholder': '0.00'}))
    fx_carry_percent = forms.CharField(required=False, label="FX Carry %", max_length=10,
                                       widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                     'label_class': BADGE_SUCCESS_CLASS,
                                                                     'id': 'fx_carry_percent', 'placeholder': '10'}))
    stub_cvr_value = forms.FloatField(required=False, label="Stub / CVR Value",
                                      widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                    'label_class': BADGE_SUCCESS_CLASS,
                                                                    'id': 'stub_cvr_value', 'placeholder': '0.00'}))
    acquirer_upside = forms.FloatField(required=False, label="Acquirer Upside",
                                       widget=forms.TextInput(attrs={'class': CUSTOM_SELECT_CLASS,
                                                                     'label_class': BADGE_SUCCESS_CLASS,
                                                                     'id': 'acquirer_upside', 'placeholder': '0.00'}))
    loss_tolerance_percentage_of_limit = forms.FloatField(required=False, label="Loss Tolerance % of Limit",
                                                          widget=forms.TextInput(attrs={'class': CUSTOM_SELECT_CLASS,
                                                                                        'label_class': BADGE_SUCCESS_CLASS,
                                                                                        'id': 'loss_tolerance_percentage_of_limit',
                                                                                        'placeholder': '10'}))
    risk_limit = forms.FloatField(required=True, label="Risk Limit",
                                  widget=forms.TextInput(attrs={'class': CUSTOM_SELECT_CLASS,
                                                                'label_class': BADGE_SUCCESS_CLASS,
                                                                'id': 'risk_limit'}))
    origination_date = forms.DateField(required=True, label="Origination Date",
                                       widget=forms.DateInput(attrs={'type': 'date', 'class': DATE_PICKER_CLASS,
                                                                     'label_class': BADGE_DARK_CLASS,
                                                                     'id': 'origination_date'}))
    position_in_acquirer = forms.CharField(label="Position in Acquirer",
                                           widget=forms.Select(choices=POSITION_ACQUIRER_CHOICES,
                                                               attrs={'class': CUSTOM_SELECT_CLASS,
                                                                      'label_class': BADGE_SUCCESS_CLASS,
                                                                      'id': 'position_in_acquirer'}))

    def clean(self):
        """
        Set the following values to 0.0 if the User did not give any input
        """
        cleaned_data = super().clean()
        if not cleaned_data.get('deal_cash_terms'):
            cleaned_data['deal_cash_terms'] = 0.0
        if not cleaned_data.get('deal_share_terms'):
            cleaned_data['deal_share_terms'] = 0.0
        if not cleaned_data.get('target_dividends'):
            cleaned_data['target_dividends'] = 0.0
        if not cleaned_data.get('acquirer_dividends'):
            cleaned_data['acquirer_dividends'] = 0.0
        if not cleaned_data.get('short_rebate'):
            cleaned_data['short_rebate'] = 0.0
        if not cleaned_data.get('fx_carry_percent'):
            cleaned_data['fx_carry_percent'] = 0.0
        if not cleaned_data.get('stub_cvr_value'):
            cleaned_data['stub_cvr_value'] = 0.0
        if not cleaned_data.get('acquirer_upside'):
            cleaned_data['acquirer_upside'] = 0.0
        if not cleaned_data.get('loss_tolerance_percentage_of_limit'):
            cleaned_data['loss_tolerance_percentage_of_limit'] = 0.0
        target_ticker = cleaned_data.get('target_ticker')
        if target_ticker:
            if 'equity' not in str(target_ticker).lower():
                cleaned_data['target_ticker'] = target_ticker.upper() + ' EQUITY'
        acquirer_ticker = cleaned_data.get('acquirer_ticker')
        if acquirer_ticker:
            if 'equity' not in str(acquirer_ticker).lower():
                cleaned_data['acquirer_ticker'] = acquirer_ticker.upper() + ' EQUITY'
        return cleaned_data


    def is_valid(self):
        """
        Validate the fields and display error message if not valid
        """
        valid = super(CreateMaDealsForm, self).is_valid()
        if not valid:
            return valid
        cleaned_data = self.cleaned_data
        if cleaned_data.get('position_in_acquirer').lower() == 'yes' and not cleaned_data.get('acquirer_ticker'):
            valid = False
            self._errors['acquirer_ticker'] = 'Acquirer Ticker is required since Position Acquirer is marked as Yes'
        if not cleaned_data.get('deal_cash_terms') and not cleaned_data.get('deal_share_terms'):
            valid = False
            self._errors['deal_cash_terms'] = 'Either Deal Cash Terms or Deal Share Terms should be present'
            self._errors['deal_share_terms'] = 'Either Deal Cash Terms or Deal Share Terms should be present'
        deal_name = cleaned_data.get('deal_name')
        slack_dict = {'deal_name': deal_name, 'action_id': cleaned_data.get('action_id'), 'analyst': cleaned_data.get('analyst'),
                      'target_ticker': cleaned_data.get('target_ticker'), 'acquirer_ticker': cleaned_data.get('acquirer_ticker'),
                      'deal_cash_terms': cleaned_data.get('deal_cash_terms'), 'deal_share_terms': cleaned_data.get('deal_share_terms'),
                      'deal_value': cleaned_data.get('deal_value'), 'target_dividends': cleaned_data.get('target_dividends'),
                      'acquirer_dividends': cleaned_data.get('acquirer_dividends'), 'short_rebate': cleaned_data.get('short_rebate'),
                      'fx_carry_percent': cleaned_data.get('fx_carry_percent'), 'stub_cvr_value': cleaned_data.get('stub_cvr_value'),
                      'acquirer_upside': cleaned_data.get('acquirer_upside'), 'risk_limit': cleaned_data.get('risk_limit'),
                      'loss_tolerance_percentage_of_limit': cleaned_data.get('loss_tolerance_percentage_of_limit'),
                      'position_in_acquirer': cleaned_data.get('position_in_acquirer')}
        if MA_Deals.objects.filter(deal_name=deal_name).exists():
            valid = False
            self._errors['deal_name'] = '{deal_name} is already present in the M&A Deal Database'.format(deal_name=deal_name)
            slack_dict['message'] = 'ERROR! Deal adready present in MA Deals'
            slack_message('new_mna_deal_notify.slack', slack_dict, channel=get_channel_name('new-mna-deals'), token=settings.SLACK_TOKEN,
                          name='ESS_IDEA_DB_ERROR_INSPECTOR')
        if FormulaeBasedDownsides.objects.filter(TradeGroup=deal_name).exists():
            valid = False
            self._errors['deal_name'] = '{deal_name} is already present in the Downside Formulae'.format(deal_name=deal_name)
            slack_dict['message'] = 'ERROR! Deal adready present in Downside Formulae'
            slack_message('new_mna_deal_notify.slack', slack_dict, channel=get_channel_name('new-mna-deals'), token=settings.SLACK_TOKEN,
                          name='ESS_IDEA_DB_ERROR_INSPECTOR')

        return valid
