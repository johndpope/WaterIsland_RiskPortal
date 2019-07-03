from django import forms

from credit_idea.models import CreditIdea


BAGDE_INFO_CLASS = 'badge badge-default badge-info'
BADGE_SUCCESS_CLASS = 'badge badge-default badge-success'
CUSTOM_SELECT_CLASS = 'custom-select form-control input-lg'
DATE_PICKER_CLASS = 'form-control'
FORM_CONTROL_CLASS = 'form-control input-lg'


class CreditIdeaForm(forms.ModelForm):
    """
    Form for Credit Idea Database
    """
    class Meta:
        model = CreditIdea
        fields = ['analyst', 'deal_bucket', 'deal_strategy_type', 'catalyst', 'catalyst_tier', 'target_sec_cusip', 'coupon',
                  'hedge_sec_cusip', 'estimated_closing_date', 'upside_price', 'downside_price', 'comments']
        labels = {
            "analyst": "Analyst",
            "deal_bucket": "Deal Bucket",
            "deal_strategy_type": "Deal Strategy Type",
            "catalyst": "Catalyst",
            "catalyst_tier": "Catalyst Tier",
            "target_sec_cusip": "Target Sec CUSIP",
            "coupon": "Coupon",
            "hedge_sec_cusip": "Hedge Sec CUSIP",
            "estimated_closing_date": "Estimated Closing Date",
            "upside_price": "Upside Price",
            "downside_price": "Downside Price",
            "comments": "Comments",
        }
        widgets = {
            'id': forms.HiddenInput(),
            "analyst": forms.TextInput(attrs={'class': FORM_CONTROL_CLASS, 'label_class': BADGE_SUCCESS_CLASS,
                                              'id': 'analyst'}),
            'deal_bucket': forms.Select(attrs={'class': CUSTOM_SELECT_CLASS, 'label_class': BADGE_SUCCESS_CLASS,
                                               'id': 'deal_bucket'}),
            "deal_strategy_type": forms.Select(attrs={'class': CUSTOM_SELECT_CLASS, 'label_class': BADGE_SUCCESS_CLASS,
                                                      'id': 'deal_strategy_type'}),
            "catalyst": forms.Select(attrs={'class': CUSTOM_SELECT_CLASS, 'label_class': BADGE_SUCCESS_CLASS,
                                            'id': 'catalyst'}),
            "catalyst_tier": forms.Select(attrs={'class': CUSTOM_SELECT_CLASS, 'label_class': BADGE_SUCCESS_CLASS,
                                                 'id': 'catalyst_tier'}),
            "target_sec_cusip": forms.TextInput(attrs={'class': FORM_CONTROL_CLASS, 'label_class': BADGE_SUCCESS_CLASS,
                                                       'id': 'target_sec_cusip'}),
            "coupon": forms.TextInput(attrs={'class': FORM_CONTROL_CLASS, 'label_class': BADGE_SUCCESS_CLASS,
                                             'id': 'coupon'}),
            "hedge_sec_cusip": forms.TextInput(attrs={'class': FORM_CONTROL_CLASS, 'label_class': BADGE_SUCCESS_CLASS,
                                                      'id': 'hedge_sec_cusip'}),
            "estimated_closing_date": forms.DateInput(attrs={'type': 'date', 'class': DATE_PICKER_CLASS,
                                                             'label_class': BAGDE_INFO_CLASS,
                                                             'id': 'estimated_closing_date'}),
            "upside_price": forms.TextInput(attrs={'class': FORM_CONTROL_CLASS, 'label_class': BADGE_SUCCESS_CLASS,
                                                   'id': 'upside_price'}),
            "downside_price": forms.TextInput(attrs={'class': FORM_CONTROL_CLASS, 'label_class': BADGE_SUCCESS_CLASS,
                                                     'id': 'downside_price'}),
            "comments": forms.Textarea(attrs={'class': FORM_CONTROL_CLASS, 'label_class': BADGE_SUCCESS_CLASS,
                                              'id': 'comments', 'rows': 8, 'cols': 40}),
        }
