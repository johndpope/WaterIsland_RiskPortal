from django import forms

from position_rec.models import AccountFundPositionRec, PositionRecAttachments


BADGE_SUCCESS_CLASS = 'badge badge-default badge-success'
FORM_CONTROL_CLASS = 'form-control input-lg'

EXLUDED_CHOICES = [
    ('No', 'No'),
    ('Yes', 'Yes')
]

class AccountFundPositionRecForm(forms.Form):
    """
    Form for Account Fun Mapping for Position Reconciliation
    """
    account_id_to_edit = forms.CharField(widget=forms.HiddenInput(attrs={'id': 'account_id_to_edit'}), required=False)
    third_party = forms.CharField(required=True, label="Custodian", max_length=100,
                                  widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                                'label_class': BADGE_SUCCESS_CLASS, 'id': 'third_party',
                                                                'placeholder': 'GS'}))
    account_no = forms.CharField(required=True, label="Account Number", max_length=50,
                                 widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                               'label_class': BADGE_SUCCESS_CLASS, 'id': 'account_no',
                                                               'placeholder': '123456789'}))
    mnemonic = forms.CharField(required=True, label="Mnemonic", max_length=50,
                               widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                             'label_class': BADGE_SUCCESS_CLASS, 'id': 'mnemonic',
                                                             'placeholder': 'Mnemonic'}))
    type = forms.CharField(required=True, label="Type", max_length=50,
                           widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                         'label_class': BADGE_SUCCESS_CLASS, 'id': 'type',
                                                         'placeholder': 'Type'}))
    fund = forms.CharField(required=True, label="Fund",
                           widget=forms.TextInput(attrs={'class': FORM_CONTROL_CLASS,
                                                         'label_class': BADGE_SUCCESS_CLASS, 'id': 'fund',
                                                         'placeholder': 'ARB'}))
    excluded = forms.CharField(required=True, label="Excluded",
                               widget=forms.Select(choices=EXLUDED_CHOICES, attrs={'class': FORM_CONTROL_CLASS,
                                                                                   'label_class': BADGE_SUCCESS_CLASS,
                                                                                   'id': 'excluded'}))

    def clean(self):
        """
        Set the following values to 0.0 if the User did not give any input
        """
        cleaned_data = super().clean()
        return cleaned_data

BADGE_SUCCESS_CLASS = 'badge badge-default badge-success'
FORM_CONTROL_CLASS = 'form-control input-lg'
class PositionRecAttachmentsForm(forms.ModelForm):
    """
    Form for uploading files for Position Reconciliation
    """
    class Meta:
        model = PositionRecAttachments
        fields = ('position_rec_attachment', 'uploaded_by', 'description')
        labels = {
            "position_rec_attachment": "Upload File",
            "description": "Description",
            "uploaded_by": "Uploaded By",
        }
        widgets = {
            'position_rec_attachment': forms.ClearableFileInput(attrs={'class': FORM_CONTROL_CLASS, 'required': True,
                                                                       'label_class': BADGE_SUCCESS_CLASS,
                                                                       'id': 'position_rec_attachment'}),
            "description": forms.Textarea(attrs={'class': FORM_CONTROL_CLASS, 'rows': 5, 'cols': 40,
                                                 'label_class': BADGE_SUCCESS_CLASS,
                                                 'id': 'description'}),
            "uploaded_by": forms.TextInput(attrs={'class': FORM_CONTROL_CLASS, 'required': True,
                                                  'label_class': BADGE_SUCCESS_CLASS,
                                                  'id': 'uploaded_by'}),
        }
