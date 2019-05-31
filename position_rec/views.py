from datetime import datetime

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import ListView, FormView, CreateView

from cleanup.models import DeleteFile
from position_rec.forms import AccountFundPositionRecForm, PositionRecAttachmentsForm
from position_rec.models import AccountFundPositionRec, PositionRecAttachments


class AccountFundPositionRecView(FormView):
    template_name = "create_account.html"
    form_class = AccountFundPositionRecForm
    success_url = '#'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = AccountFundPositionRec.objects.all()
        context['account_list'] = queryset
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        account_id_to_edit = self.request.POST.get('account_id_to_edit')
        third_party = data.get('third_party')
        account_no = data.get('account_no')
        mnemonic = data.get('mnemonic')
        type = data.get('type')
        fund = data.get('fund')
        excluded = data.get('excluded')
        date_updated = datetime.now()
        create_new_account = False if account_id_to_edit else True
        if not create_new_account:
            try:
                account_obj = AccountFundPositionRec.objects.get(id=account_id_to_edit)
                account_obj.third_party = third_party
                account_obj.account_no = account_no
                account_obj.mnemonic = mnemonic
                account_obj.type = type
                account_obj.fund = fund
                account_obj.excluded = excluded
                account_obj.date_updated = date_updated
                account_obj.save()
                create_new_account = False
            except AccountFundPositionRec.DoesNotExist:
                create_new_account = True
        if create_new_account:
            AccountFundPositionRec.objects.create(third_party=third_party, account_no=account_no,
                                                  mnemonic=mnemonic, type=type, fund=fund, excluded=excluded,
                                                  date_updated=date_updated)
        return super(AccountFundPositionRecView, self).form_valid(form)


def get_account_details(request):
    """ Retreives all the details for the requested Account """
    if request.method == 'POST':
        account_id = request.POST['account_id']
        account_details = {}
        try:
            account = AccountFundPositionRec.objects.get(id=account_id)
            account_details['third_party'] = account.third_party
            account_details['account_no'] = account.account_no
            account_details['mnemonic'] = account.mnemonic
            account_details['type'] = account.type
            account_details['fund'] = account.fund
            account_details['excluded'] = account.excluded
        except AccountFundPositionRec.DoesNotExist:
            account_details = []

    return JsonResponse({'account_details': account_details})


def delete_account(request):
    response = None
    if request.method == 'POST':
        # Take the ID and Delete
        id_to_delete = request.POST['id']
        AccountFundPositionRec.objects.get(id=id_to_delete).delete()
        response = 'account_deleted'

    return HttpResponse(response)


class PositionRecAttachmentsView(FormView):
    template_name = 'file_upload.html'
    form_class = PositionRecAttachmentsForm
    success_url = '#'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = PositionRecAttachments.objects.all()
        context['uploaded_file_list'] = queryset
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        original_filename = 'filename'
        position_rec_attachment = data.get('position_rec_attachment')
        if isinstance(position_rec_attachment, InMemoryUploadedFile):
            original_filename = position_rec_attachment._name
        description = data.get('description')
        uploaded_by = data.get('uploaded_by')
        uploaded_on = datetime.now().date()
        PositionRecAttachments.objects.create(position_rec_attachment=position_rec_attachment,
                                              original_filename=original_filename, description=description,
                                              uploaded_by=uploaded_by, uploaded_on=uploaded_on)
        return super(PositionRecAttachmentsView, self).form_valid(form)


def delete_ops_file(request):
    response = None
    if request.method == 'POST':
        try:
            id_to_delete = request.POST['id']
            file_object = PositionRecAttachments.objects.get(id=id_to_delete)
            file_field = file_object.position_rec_attachment
            file_object.delete()
            response = 'file_deleted'
            DeleteFile(file_details=file_field, aws_file_key=file_field.file.obj.key,
                       aws_bucket=file_field.file.obj.bucket_name, requested_delete_at=datetime.now()).save()
        except Exception as error:
            response = 'Error'
            print('ERROR', error)
    return HttpResponse(response)
    
