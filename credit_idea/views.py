import bbgclient
from datetime import date, datetime, timedelta
import json
import pandas as pd

from django.db import connection
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from credit_idea.forms import CreditIdeaForm
from credit_idea.models import CreditIdea, CreditIdeaDetails, CreditIdeaScenario
from risk.models import MA_Deals
from risk_reporting.models import FormulaeBasedDownsides


class CreditIdeaView(FormView):
    """
    View for creating, editing and delete Credit Idea.
    """
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
        arb_tradegroup = data.get('arb_tradegroup')
        arb_tradegroup = arb_tradegroup.upper() if arb_tradegroup else arb_tradegroup
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
                account_obj.arb_tradegroup = arb_tradegroup
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
            credit_idea = CreditIdea.objects.create(deal_bucket=deal_bucket, deal_strategy_type=deal_strategy_type,
                                                    catalyst=catalyst, catalyst_tier=catalyst_tier,
                                                    target_sec_cusip=target_sec_cusip, coupon=coupon,
                                                    hedge_sec_cusip=hedge_sec_cusip, analyst=analyst,
                                                    estimated_closing_date=estimated_closing_date,
                                                    upside_price=upside_price, downside_price=downside_price,
                                                    arb_tradegroup=arb_tradegroup, comments=comments)
            try:
                formulaue_downside_values = FormulaeBasedDownsides.objects.get(TradeGroup__exact=arb_tradegroup,
                                                                               TargetAcquirer__exact='Target')
                topping_big_upside = convert_to_float_else_zero(formulaue_downside_values.DealValue)
                base_case_downside = convert_to_float_else_zero(formulaue_downside_values.base_case)
                outlier_downside = convert_to_float_else_zero(formulaue_downside_values.outlier)
                base_case_downside_type = formulaue_downside_values.BaseCaseDownsideType
                outlier_downside_type = formulaue_downside_values.OutlierDownsideType
            except FormulaeBasedDownsides.DoesNotExist:
                topping_big_upside = 0
                base_case_downside = 0
                outlier_downside = 0
                base_case_downside_type = ''
                outlier_downside_type = ''
            try:
                ma_deals_object = MA_Deals.objects.get(deal_name__exact=arb_tradegroup)
                deal_value = ma_deals_object.deal_value
                target_ticker = ma_deals_object.target_ticker
                acq_ticker = ma_deals_object.acquirer_ticker
                cash_consideration = ma_deals_object.deal_cash_terms
                share_consideration = ma_deals_object.deal_share_terms
                target_dividend = ma_deals_object.target_dividends
                acq_dividend = ma_deals_object.acquirer_dividends
            except MA_Deals.DoesNotExist:
                deal_value = 0
                target_ticker = ''
                acq_ticker = ''
                cash_consideration = 0
                share_consideration = 0
                target_dividend = 0
                acq_dividend = 0
            query = "SELECT AUM, ClosingDate FROM wic.daily_flat_file_db WHERE Flat_file_as_of = (SELECT " \
                    "MAX(flat_file_as_of) from wic.daily_flat_file_db) and Fund='ARB' and TradeGroup='" + \
                    arb_tradegroup.upper() + "';"
            flat_file_df = pd.read_sql_query(query, con=connection)
            if not flat_file_df.empty:
                fund_assets = flat_file_df.at[flat_file_df.index[0], 'AUM']
                closing_date = flat_file_df.at[flat_file_df.index[0], 'ClosingDate']
            else:
                fund_assets = 0

            CreditIdeaDetails.objects.create(target_ticker=target_ticker, topping_big_upside=topping_big_upside,
                                             base_case_downside=base_case_downside, outlier_downside=outlier_downside,
                                             acq_ticker=acq_ticker, cash_consideration=cash_consideration,
                                             share_consideration=share_consideration, deal_value=deal_value,
                                             target_dividend=target_dividend, acq_dividend=acq_dividend,
                                             fund_assets=fund_assets, float_so=0, acq_pb_rate=0, target_pb_rate=0,
                                             base_case_downside_type=base_case_downside_type,
                                             outlier_downside_type=outlier_downside_type, credit_idea=credit_idea)
            scenario_keys = ['Earlier Date', 'Base Date', 'Worst Date']
            if closing_date and isinstance(closing_date, (date, datetime)):
                date_list = [closing_date - timedelta(days=31), closing_date, closing_date + timedelta(days=31)]
            else:
                date_list = ['', '', '']
            for index, scenario in enumerate(scenario_keys):
                CreditIdeaScenario.objects.create(scenario=scenario, credit_idea=credit_idea,
                                                  estimated_closing_date=date_list[index])

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
                credit_idea_details['arb_tradegroup'] = credit_idea.arb_tradegroup
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


class CreditIdeaDetailsView(TemplateView):
    template_name = 'view_credit_idea.html'

    def post(self, request, *args, **kwargs):
        try:
            context = self.get_context_data()
            credit_idea_id = request.POST.get('credit_idea_id')
            master_data = json.loads(request.POST.get('master_data'))
            for key in master_data:
                if 'scenario' in key.lower():
                    scenario_data = master_data.get('scenario_data')
                    credit_idea_scenarios = CreditIdeaScenario.objects.filter(credit_idea_id=credit_idea_id)
                    for data in scenario_data:
                        credit_idea_scenario, created = credit_idea_scenarios.get_or_create(id=data.get('database_id'),
                                                                                            credit_idea_id=credit_idea_id)
                        credit_idea_scenario.scenario = data.get('scenario')
                        credit_idea_scenario.last_price = data.get('last_price') or 0
                        credit_idea_scenario.dividends = data.get('dividends') or 0
                        credit_idea_scenario.rebate = data.get('rebate') or 0
                        credit_idea_scenario.hedge = data.get('hedge') or 0
                        credit_idea_scenario.deal_value = data.get('deal_value') or 0
                        credit_idea_scenario.spread = data.get('spread') or 0
                        credit_idea_scenario.gross_pct = data.get('gross_pct') or 0
                        credit_idea_scenario.annual_pct = data.get('annual_pct') or 0
                        credit_idea_scenario.days_to_close = data.get('days_to_close') or 0
                        credit_idea_scenario.dollars_to_make = data.get('dollars_to_make') or 0
                        credit_idea_scenario.dollars_to_lose = data.get('dollars_to_lose') or 0
                        credit_idea_scenario.implied_prob = data.get('implied_prob') or 0
                        credit_idea_scenario.estimated_closing_date = data.get('exp_close')
                        credit_idea_scenario.save()
                if 'credit_idea_details' in key.lower():
                    try:
                        credit_idea_details_object = CreditIdeaDetails.objects.get(credit_idea_id=credit_idea_id)
                        credit_idea_details = master_data.get('credit_idea_details')
                        credit_idea_details_object.topping_big_upside = credit_idea_details.get('upside_value_upside')
                        credit_idea_details_object.base_case_downside = credit_idea_details.get('upside_value_base_downside')
                        credit_idea_details_object.outlier_downside = credit_idea_details.get('upside_value_outlier_downside')
                        credit_idea_details_object.target_ticker = credit_idea_details.get('deal_terms_target_ticker')
                        credit_idea_details_object.acq_ticker = credit_idea_details.get('deal_terms_acq_ticker')
                        credit_idea_details_object.cash_consideration = credit_idea_details.get('deal_terms_value_cash')
                        credit_idea_details_object.share_consideration = credit_idea_details.get('deal_terms_value_share')
                        credit_idea_details_object.deal_value = credit_idea_details.get('deal_terms_value_deal_value')
                        credit_idea_details_object.target_dividend = credit_idea_details.get('deal_terms_value_target_dividend')
                        credit_idea_details_object.acq_dividend = credit_idea_details.get('deal_terms_value_acq_dividend')
                        credit_idea_details_object.fund_assets = credit_idea_details.get('sizing_val_fund_assets')
                        credit_idea_details_object.float_so = credit_idea_details.get('sizing_val_float_so')
                        credit_idea_details_object.acq_pb_rate = credit_idea_details.get('rebate_acq_val_pb_rate')
                        credit_idea_details_object.target_pb_rate = credit_idea_details.get('rebate_target_val_pb_rate')
                        credit_idea_details_object.nav_pct_impact = credit_idea_details.get('passive_value_nav_impact')
                        credit_idea_details_object.save()
                    except CreditIdeaDetails.DoesNotExist:
                        response = 'failed'
            response = 'success'
        except Exception:
            response='failed'
        return HttpResponse(response)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        credit_idea_id = self.request.GET.get('credit_idea_id')
        if credit_idea_id:
            try:
                credit_idea_object = CreditIdea.objects.get(id=credit_idea_id)
                credit_idea_details = CreditIdeaDetails.objects.get(credit_idea_id=credit_idea_id)
                credit_idea_scenarios = CreditIdeaScenario.objects.filter(credit_idea_id=credit_idea_id)
                arb_tradegroup = credit_idea_object.arb_tradegroup
                arb_base_case = credit_idea_details.base_case_downside or 0
                deal_value = credit_idea_details.deal_value or 0
                arb_outlier = credit_idea_details.outlier_downside or 0
                arb_base_case_downside_type = credit_idea_details.base_case_downside_type
                arb_outlier_downside_type = credit_idea_details.outlier_downside_type
                target_ticker = credit_idea_details.target_ticker
                acq_ticker = credit_idea_details.acq_ticker
                cash_terms = convert_to_float_else_zero(credit_idea_details.cash_consideration)
                share_terms = convert_to_float_else_zero(credit_idea_details.share_consideration)
                target_dividends = convert_to_float_else_zero(credit_idea_details.target_dividend)
                acq_dividends = convert_to_float_else_zero(credit_idea_details.acq_dividend)
                acq_pb_rate = convert_to_float_else_zero(credit_idea_details.acq_pb_rate)
                target_pb_rate = convert_to_float_else_zero(credit_idea_details.target_pb_rate)
                fund_assets = credit_idea_details.fund_assets
                float_so_value = credit_idea_details.float_so
                nav_pct_impact = convert_to_float_else_zero(credit_idea_details.nav_pct_impact)

            except CreditIdea.DoesNotExist:
                raise Http404('You have not uploaded any File to support this Model!!')
            except CreditIdeaDetails.DoesNotExist:
                arb_base_case = 0
                deal_value = 0
                arb_outlier = 0
                arb_base_case_downside_type = ''
                arb_outlier_downside_type = ''
                target_ticker = ''
                acq_ticker = ''
                cash_terms = 0
                share_terms = 0
                target_dividends = 0
                acq_dividends = 0
                acq_pb_rate = 0
                target_pb_rate = 0
                fund_assets = 0
                float_so_value = 0
                nav_pct_impact = 0
            try:
                api_host = bbgclient.bbgclient.get_next_available_host()
                bbg_target_ticker = target_ticker.upper() + ' EQUITY' if 'equity' not in target_ticker.lower() else target_ticker.upper()
                bbg_acq_ticker = acq_ticker.upper() + ' EQUITY' if 'equity' not in acq_ticker.lower() else acq_ticker.upper()
                bbg_fed_fund_index = 'FEDL01 INDEX'
                tickers_live_price = [bbg_target_ticker, bbg_acq_ticker, bbg_fed_fund_index]
                live_price = bbgclient.bbgclient.get_secid2field(tickers_live_price, 'tickers',
                                                                 ['PX_LAST', 'DVD_SH_LAST'], req_type='refdata',
                                                                 api_host=api_host)

                target_live_price, acq_last_price, fed_funds_last_price = 0, 0, 0
                target_ticker_price = live_price.get(bbg_target_ticker)
                if target_ticker_price:
                    px_last_value = target_ticker_price.get('PX_LAST')
                    target_live_price = px_last_value[0] if len(px_last_value) > 0 else 0
                    target_live_price = convert_to_float_else_zero(target_live_price)
                    dvd_last_value = target_ticker_price.get('DVD_SH_LAST')
                    tgt_dvd = dvd_last_value[0] if len(dvd_last_value) > 0 else 0
                    tgt_dvd = convert_to_float_else_zero(tgt_dvd)

                acq_ticker_price = live_price.get(bbg_acq_ticker)
                if acq_ticker_price:
                    px_last_value = acq_ticker_price.get('PX_LAST')
                    acq_last_price = px_last_value[0] if len(px_last_value) > 0 else 0
                    acq_last_price = convert_to_float_else_zero(acq_last_price)
                    dvd_last_value = target_ticker_price.get('DVD_SH_LAST')
                    acq_dvd = dvd_last_value[0] if len(dvd_last_value) > 0 else 0
                    acq_dvd = convert_to_float_else_zero(acq_dvd)
                
                fed_fund_price = live_price.get(bbg_fed_fund_index)
                if fed_fund_price:
                    px_last_value = fed_fund_price.get('PX_LAST')
                    fed_funds_last_price = px_last_value[0] if len(px_last_value) > 0 else 0
                    fed_funds_last_price = convert_to_float_else_zero(fed_funds_last_price)

                acquirer_premium = 30
                acquirer_30_premium = (1 + (acquirer_premium * 0.01)) * acq_last_price
                topping_break_spread = ((acquirer_30_premium * share_terms) + cash_terms) - arb_base_case
                downsides_data = [
                    {'id': 'upside', 'key': 'Topping Bid Upside', 'type': 'Deal Value', 'value': round(deal_value, 2)},
                    {'id': 'base_downside', 'key': 'Base Case Downside', 'type': arb_base_case_downside_type, 'value': round(arb_base_case, 2)},
                    {'id': 'outlier_downside', 'key': 'Outlier Downside', 'type': arb_outlier_downside_type, 'value': round(arb_outlier, 2)},
                    {'id': 'thirty_premium', 'key': 'Acquirer 30% Premium', 'type': str(acquirer_premium) + ' %', 'value': round(acquirer_30_premium, 2)},
                    {'id': 'normal_spread', 'key': 'Normal Break Spread', 'type': 'Break Spread', 'value': round(target_live_price - arb_base_case, 2)},
                    {'id': 'topping_spread', 'key': 'Topping Break Spread', 'type': 'Break Spread', 'value': round(topping_break_spread, 2)}
                ]
                gross_spread = convert_to_float_else_zero(deal_value) - convert_to_float_else_zero(target_live_price)
                dvd_adjusted_spread = gross_spread + target_dividends
                target_live_price = round(target_live_price, 2)
                dvd_adjusted_spread = convert_to_float_else_zero(gross_spread + target_dividends - acq_dividends * share_terms)
                base_scenario = credit_idea_scenarios.filter(scenario='Base Date')
                if base_scenario.exists():
                    estimated_closing_date = base_scenario[0].estimated_closing_date
                    if isinstance(estimated_closing_date, (date, datetime)):
                        estimated_closing_date = estimated_closing_date.strftime('%m/%d/%Y')
                    base_rebate = convert_to_float_else_zero(base_scenario[0].rebate)
                else:
                    estimated_closing_date = ''
                    base_rebate = 0
                rebate_adjusted_spread = convert_to_float_else_zero(dvd_adjusted_spread + base_rebate)
                spread_data = [
                    {'id': 'target_ticker', 'key': 'Target Ticker', 'type_input': 'true', 'type': target_ticker,
                     'type_input2': 'true', 'value': target_live_price},
                    {'id': 'acq_ticker', 'key': 'Acq. Ticker (N/A for PE)', 'type_input': 'true', 'type': acq_ticker,
                     'type_input2': 'true', 'value': round(acq_last_price, 2)},
                    {'id': 'cash', 'key': 'Cash Consideration', 'type_input': 'false', 'type': '',
                     'type_input2': 'true', 'value': cash_terms},
                    {'id': 'share', 'key': 'Share Considerations', 'type_input': 'false', 'type': '',
                     'type_input2': 'true', 'value': share_terms},
                    {'id': 'deal_value', 'key': 'Current Deal Value', 'type_input': 'false', 'type': '',
                     'type_input2': 'false', 'value': deal_value},
                    {'id': 'curr_price', 'key': target_ticker + ' Current Price', 'type_input': 'false', 'type': '',
                     'type_input2': 'false', 'value': target_live_price},
                    {'id': 'gross_spread', 'key': 'Gross Spread', 'type_input': 'false', 'type': '',
                     'type_input2': 'false', 'value': round(gross_spread, 2)},
                    {'id': 'target_dividend', 'key': 'Target Dividend', 'type_input': 'false', 'type': '',
                     'type_input2': 'true', 'value': target_dividends},
                    {'id': 'acq_dividend', 'key': 'Acquirer Dividend', 'type_input': 'false', 'type': '',
                     'type_input2': 'true', 'value': acq_dividends},
                    {'id': 'dvd_adjusted_spread', 'key': 'DVD Adjusted Spread', 'type_input': 'false', 'type': '',
                     'type_input2': 'false', 'value': round(dvd_adjusted_spread, 2)},
                    {'id': 'rebate_adjusted_spread', 'key': 'Rebate Adjusted Spread to', 'type_input': 'false',
                     'type': estimated_closing_date, 'type_input2': 'false', 'value': round(rebate_adjusted_spread, 2)}
                ]
                acq_rebate_pct = fed_funds_last_price - acq_pb_rate
                target_rebate_pct = fed_funds_last_price - target_pb_rate
                rebate_data = [
                    {'id': 'funds_rate', 'type_input': 'true', 'key': 'Fed Funds Rate', 'acq_value': round(fed_funds_last_price, 2),
                     'target_value': round(fed_funds_last_price, 2)},
                    {'id': 'pb_rate', 'type_input': 'true', 'key': 'Less: PB Rate', 'acq_value': acq_pb_rate, 'target_value': target_pb_rate},
                    {'id': 'rebate_pct', 'type_input': 'false', 'key': 'Rebate %', 'acq_value': acq_rebate_pct, 'target_value': target_rebate_pct},
                ]

                five_percent_cap = convert_to_float_else_zero(float_so_value) * 0.05
                if convert_to_float_else_zero(fund_assets) != 0:
                    capacity = five_percent_cap * target_live_price / fund_assets * 100
                else:
                    capacity = 0
                sizing_data = [
                    {'id': 'fund_assets', 'type_input': 'true', 'key': 'Fund Assets ($)', 'value': fund_assets},
                    {'id': 'float_so', 'type_input': 'true', 'key': 'Float S/O', 'value': float_so_value},
                    {'id': 'five_cap', 'type_input': 'false', 'key': '5% cap', 'value': five_percent_cap},
                    {'id': 'capacity', 'type_input': 'false', 'key': 'Capacity', 'value': round(capacity, 2)}
                ]
                size_in_shares = abs(nav_pct_impact * 0.01 * fund_assets) / (topping_break_spread - gross_spread)
                passive_spend = size_in_shares * target_live_price
                passive_pct_aum = passive_spend / fund_assets * 100
                passive_data = [
                    {'id': 'nav_impact', 'type_input': 'true', 'key': 'NAV % impact', 'value': nav_pct_impact},
                    {'id': 'size_shares', 'type_input': 'false', 'key': 'Size in shares', 'value': round(size_in_shares)},
                    {'id': 'spend', 'type_input': 'false', 'key': 'Spend', 'value': round(passive_spend)},
                    {'id': 'aum', 'type_input': 'false', 'key': '% AUM', 'value': round(passive_pct_aum, 2)}
                ]
                # scenario_dividends = target_dividends_type * target_dividends

                scenario_data = []
                keys = ['id', 'credit_idea_id', 'scenario', 'last_price', 'dividends', 'rebate', 'hedge', 'deal_value',
                        'spread', 'gross_pct', 'annual_pct', 'days_to_close', 'dollars_to_make', 'dollars_to_lose',
                        'implied_prob', 'estimated_closing_date']
                scenario_count = 1
                for scenario in credit_idea_scenarios:
                    temp_dict = {key: getattr(scenario, key) for key in keys}
                    temp_dict['estimated_closing_date'] = temp_dict['estimated_closing_date'].strftime('%Y-%m-%d') if \
                    temp_dict['estimated_closing_date'] else temp_dict['estimated_closing_date']
                    temp_dict['database_id'] = temp_dict.get('id')
                    temp_dict['last_price'] = round(target_live_price, 2)
                    temp_dict['dividends'] = target_dividends
                    temp_dict['implied_prob'] = round(convert_to_float_else_zero(1 - (gross_spread / topping_break_spread)), 2)
                    temp_dict['dollars_to_lose'] = round(convert_to_float_else_zero((gross_spread - topping_break_spread) * size_in_shares), 2)
                    temp_dict['DT_RowId'] = 'scenario_row_' + str(scenario_count)
                    scenario_data.append(temp_dict)
                    scenario_count += 1
            except Exception:
                downsides_data, spread_data, rebate_data, sizing_data = [], [], [], []
                scenario_data, passive_data = [], []
            context.update({
                'arb_tradegroup': arb_tradegroup.upper(),
                'downsides_data': json.dumps(downsides_data),
                'spread_data': json.dumps(spread_data),
                'rebate_data': json.dumps(rebate_data),
                'sizing_data': json.dumps(sizing_data),
                'scenario_data': json.dumps(scenario_data),
                'passive_data': json.dumps(passive_data),
            })
        return context


def calculate_number_of_days(target_date):
    """
    Returns number of days from the given date till today
    """
    if target_date:
        if isinstance(target_date, (datetime)):
            return (target_date - datetime.now()).days
        elif isinstance(target_date, (date)):
            return (target_date - date.today()).days
    return 0


def convert_to_float_else_zero(value):
    if value:
        try:
            return float(value)
        except ValueError:
            return 0
    else:
        return 0
