from datetime import datetime

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic.edit import FormView

from credit_idea.forms import CreditIdeaForm
from credit_idea.models import CreditIdea


class CreditIdeaView(FormView):
    template_name = 'credit_idea_db.html'
    form_class = CreditIdeaForm
    fields = '__all__'
    success_url = '#'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = CreditIdea.objects.all()
        context['credit_idea_list'] = queryset
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        idea_id_to_edit = self.request.POST.get('id')
        analyst = data.get('analyst')
        deal_bucket = data.get('deal_bucket')
        deal_strategy_type = data.get('deal_strategy_type')
        catalyst = data.get('catalyst')
        catalyst_tier = data.get('catalyst_tier')
        target_sec_cusip = data.get('target_sec_cusip')
        coupon = data.get('coupon')
        hedge_sec_cusip = data.get('hedge_sec_cusip')
        estimated_closing_date = data.get('estimated_closing_date')
        upside_price = data.get('upside_price')
        downside_price = data.get('downside_price')
        comments = data.get('comments')
        create_new_idea = False if idea_id_to_edit else True
        if not create_new_idea:
            try:
                account_obj = CreditIdea.objects.get(id=idea_id_to_edit)
                account_obj.analyst = analyst
                account_obj.deal_bucket = deal_bucket
                account_obj.deal_strategy_type = deal_strategy_type
                account_obj.catalyst = catalyst
                account_obj.catalyst_tier = catalyst_tier
                account_obj.target_sec_cusip = target_sec_cusip
                account_obj.coupon = coupon
                account_obj.hedge_sec_cusip = hedge_sec_cusip
                account_obj.estimated_closing_date = estimated_closing_date
                account_obj.upside_price = upside_price
                account_obj.downside_price = downside_price
                account_obj.comments = comments
                account_obj.save()
                create_new_idea = False
            except CreditIdea.DoesNotExist:
                create_new_idea = True
        if create_new_idea:
            CreditIdea.objects.create(deal_bucket=deal_bucket, deal_strategy_type=deal_strategy_type, catalyst=catalyst,
                                      catalyst_tier=catalyst_tier, target_sec_cusip=target_sec_cusip, coupon=coupon,
                                      hedge_sec_cusip=hedge_sec_cusip, estimated_closing_date=estimated_closing_date,
                                      upside_price=upside_price, downside_price=downside_price, analyst=analyst,
                                      comments=comments)
        return super(CreditIdeaView, self).form_valid(form)


def get_credit_idea_details(request):
    """ Retreives all the details for the requested Credit IDEA """
    credit_idea_details = []
    if request.method == 'GET':
        credit_idea_id = request.GET.get('credit_idea_id')
        if credit_idea_id:
            try:
                credit_idea_details = {}
                credit_idea = CreditIdea.objects.get(id=credit_idea_id)
                credit_idea_details['analyst'] = credit_idea.analyst
                credit_idea_details['deal_bucket'] = credit_idea.deal_bucket
                credit_idea_details['deal_strategy_type'] = credit_idea.deal_strategy_type
                credit_idea_details['catalyst'] = credit_idea.catalyst
                credit_idea_details['catalyst_tier'] = credit_idea.catalyst_tier
                credit_idea_details['target_sec_cusip'] = credit_idea.target_sec_cusip
                credit_idea_details['coupon'] = credit_idea.coupon
                credit_idea_details['hedge_sec_cusip'] = credit_idea.hedge_sec_cusip
                credit_idea_details['estimated_closing_date'] = credit_idea.estimated_closing_date
                credit_idea_details['upside_price'] = credit_idea.upside_price
                credit_idea_details['downside_price'] = credit_idea.downside_price
                credit_idea_details['comments'] = credit_idea.comments
            except CreditIdea.DoesNotExist:
                credit_idea_details = []

    return JsonResponse({'credit_idea_details': credit_idea_details})


def delete_credit_idea(request):
    response = None
    if request.method == 'POST':
        # Take the ID and Delete
        id_to_delete = request.POST['id']
        CreditIdea.objects.get(id=id_to_delete).delete()
        response = 'credit_idea_deleted'

    return HttpResponse(response)
