import datetime

from django.conf import settings
from django.shortcuts import render
from django.views.generic.edit import FormView
from django_slack import slack_message

from bbgclient import bbgclient
from mna_deal.forms import CreateMaDealsForm
from risk.models import MA_Deals
from risk_reporting.models import FormulaeBasedDownsides


API_HOST = bbgclient.get_next_available_host()
DATE_TODAY = datetime.datetime.now().date()


class CreateMaDealsView(FormView):
    """Views for Creating a new M & A Deal"""
    template_name = 'create_mna_deal.html'
    form_class = CreateMaDealsForm
    fields = '__all__'

    def get_success_url(self):
        """Redirect the User back to the referal page"""
        http_referer = self.request.META.get('HTTP_REFERER')
        if 'mna_idea_database' in http_referer or 'formula_based_downsides' in http_referer:
            return http_referer
        else:
            return '#'

    def form_valid(self, form):
        """Create the objects in respective models if the form is valid"""
        data = form.cleaned_data
        action_id = self.request.POST.get('action_id')
        deal_name = data.get('deal_name')
        analyst = data.get('analyst')
        target_ticker = data.get('target_ticker')
        acquirer_ticker = data.get('acquirer_ticker')
        deal_cash_terms = data.get('deal_cash_terms')
        deal_share_terms = data.get('deal_share_terms')
        deal_value = data.get('deal_value')
        expected_close_date = data.get('expected_close_date')
        target_dividends = data.get('target_dividends')
        acquirer_dividends = data.get('acquirer_dividends')
        short_rebate = data.get('short_rebate')
        fx_carry_percent = data.get('fx_carry_percent')
        stub_cvr_value = data.get('stub_cvr_value')
        acquirer_upside = data.get('acquirer_upside')
        loss_tolerance_percentage_of_limit = data.get('loss_tolerance_percentage_of_limit')
        status = 'ACTIVE'
        created = DATE_TODAY
        risk_limit = data.get('risk_limit')
        origination_date = data.get('origination_date')
        position_in_acquirer = data.get('position_in_acquirer')
        latest_object = FormulaeBasedDownsides.objects.filter(id__isnull=False).latest('id')
        max_id = latest_object.id if latest_object and latest_object.id else -1
        insert_id = max_id + 1

        # Save to MA Deal Model
        deal_object = MA_Deals(action_id=action_id, deal_name=deal_name, analyst=analyst, target_ticker=target_ticker,
                               acquirer_ticker=acquirer_ticker, deal_cash_terms=deal_cash_terms,
                               deal_share_terms=deal_share_terms, deal_value=deal_value,
                               expected_closing_date=expected_close_date, target_dividends=target_dividends,
                               acquirer_dividends=acquirer_dividends, short_rebate=short_rebate,
                               fx_carry_percent=fx_carry_percent, stub_cvr_value=stub_cvr_value,
                               acquirer_upside=acquirer_upside, status=status, created=created,
                               loss_tolerance_percentage_of_limit=loss_tolerance_percentage_of_limit,
                               last_modified=DATE_TODAY, is_complete='No')
        deal_object.save()

        # Calculate Last Price and Save to FormulaeBasedDownsides Model for Target
        try:
            target_last_price = float(bbgclient.get_secid2field([target_ticker], 'tickers', ['CRNCY_ADJ_PX_LAST'],
                                                                req_type='refdata', api_host=API_HOST)[target_ticker]
                                                                ['CRNCY_ADJ_PX_LAST'][0]) if deal_share_terms > 0 else 0
        except Exception as error:
            target_last_price = None
        target_object = FormulaeBasedDownsides(id=insert_id, TradeGroup=deal_name, Underlying=target_ticker,
                                               TargetAcquirer='Target', Analyst=analyst, RiskLimit=risk_limit,
                                               OriginationDate=origination_date, DealValue=deal_value,
                                               LastPrice=target_last_price)
        target_object.save()

        # If Position in Acquirer is Yes then calculate last price and save to FormulaeBasedDownsides Model for Acquirer
        if position_in_acquirer.lower() == 'yes':
            try:
                acquirer_last_price = float(bbgclient.get_secid2field([target_ticker], 'tickers', ['CRNCY_ADJ_PX_LAST'],
                                                                      req_type='refdata', api_host=API_HOST)[target_ticker]
                                                                      ['CRNCY_ADJ_PX_LAST'][0]) if deal_share_terms > 0 else 0
            except Exception as error:
                acquirer_last_price = None
            acquirer_object = FormulaeBasedDownsides(id=insert_id+1, TradeGroup=deal_name, Underlying=acquirer_ticker,
                                                     TargetAcquirer='Acquirer', Analyst=analyst, RiskLimit=risk_limit,
                                                     OriginationDate=origination_date, DealValue=deal_value,
                                                     LastPrice=acquirer_last_price)
            acquirer_object.save()
        slack_message('new_mna_deal_notify.slack',
                      {'message': 'New M & A Deal Added', 'deal_name': deal_name, 'action_id': action_id, 'analyst': analyst,
                      'target_ticker': target_ticker, 'acquirer_ticker': acquirer_ticker, 'deal_cash_terms': deal_cash_terms,
                      'deal_share_terms': deal_share_terms, 'deal_value': deal_value, 'target_dividends': target_dividends,
                      'acquirer_dividends': acquirer_dividends, 'short_rebate': short_rebate, 'fx_carry_percent': fx_carry_percent,
                      'stub_cvr_value': stub_cvr_value, 'acquirer_upside': acquirer_upside,
                      'loss_tolerance_percentage_of_limit': loss_tolerance_percentage_of_limit, 'risk_limit': risk_limit,
                      'position_in_acquirer': position_in_acquirer},
                    channel='new-mna-deals',
                    token=settings.SLACK_TOKEN,
                    name='ESS_IDEA_DB_ERROR_INSPECTOR')
        return super(CreateMaDealsView, self).form_valid(form)
