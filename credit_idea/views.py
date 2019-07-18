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
from credit_idea.models import (CreditIdea, CreditIdeaCreditDetails, CreditIdeaDetails, CreditIdeaCreditScenario,
    CreditIdeaScenario)
from risk.models import MA_Deals
from risk_reporting.models import FormulaeBasedDownsides


ACQUIRER_PREMIUM = 30
NAV_PCT_IMPACT = -0.15
ACQ_PB_RATE = 0.40
TARGET_PB_RATE = 0.40
FACE_VALUE_OF_BONDS = 1000000
PROPOSED_RATIO = 5.00


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
                topping_big_upside = 0.00
                base_case_downside = 0.00
                outlier_downside = 0.00
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
                deal_value = 0.00
                target_ticker = ''
                acq_ticker = ''
                cash_consideration = 0.00
                share_consideration = 0.00
                target_dividend = 0.00
                acq_dividend = 0.00
            query = "SELECT AUM, ClosingDate FROM wic.daily_flat_file_db WHERE Flat_file_as_of = (SELECT " \
                    "MAX(flat_file_as_of) from wic.daily_flat_file_db) and Fund='ARB' and TradeGroup='" + \
                    arb_tradegroup.upper() + "';"
            flat_file_df = pd.read_sql_query(query, con=connection)
            if not flat_file_df.empty:
                fund_assets = flat_file_df.at[flat_file_df.index[0], 'AUM']
                closing_date = flat_file_df.at[flat_file_df.index[0], 'ClosingDate']
            else:
                fund_assets = 0.00
                closing_date = date.today()

            CreditIdeaDetails.objects.create(target_ticker=target_ticker, topping_big_upside=topping_big_upside,
                                             base_case_downside=base_case_downside, outlier_downside=outlier_downside,
                                             acq_ticker=acq_ticker, cash_consideration=cash_consideration,
                                             share_consideration=share_consideration, deal_value=deal_value,
                                             target_dividend=target_dividend, acq_dividend=acq_dividend,
                                             fund_assets=fund_assets, float_so=0, acq_pb_rate=ACQ_PB_RATE,
                                             target_pb_rate=TARGET_PB_RATE, nav_pct_impact=NAV_PCT_IMPACT,
                                             base_case_downside_type=base_case_downside_type, credit_idea=credit_idea,
                                             outlier_downside_type=outlier_downside_type)
            CreditIdeaCreditDetails.objects.create(credit_idea=credit_idea, face_value_of_bonds=FACE_VALUE_OF_BONDS,
                                                   proposed_ratio=PROPOSED_RATIO)
            scenario_keys = ['Earlier Date', 'Base Date', 'Worst Date']
            scenario_hedge_keys = ['Bonds Called (Redemption)', 'Change of Control (CoC)', 'No Deal (Base Case)',
                                   'No Deal (Conservative Case)']
            if closing_date and isinstance(closing_date, (date, datetime)):
                days_to_close = calculate_number_of_days(closing_date)
                date_list = [closing_date - timedelta(days=31), closing_date, closing_date + timedelta(days=31)]
            else:
                date_list = ['', '', '']
                days_to_close = 0
            for index, scenario in enumerate(scenario_keys):
                CreditIdeaScenario.objects.create(scenario=scenario, credit_idea=credit_idea,
                                                  estimated_closing_date=date_list[index])
            for scenario in scenario_hedge_keys:
                CreditIdeaCreditScenario.objects.create(scenario=scenario, credit_idea=credit_idea, is_hedge=False,
                                                        returns_estimated_closing_date=closing_date,
                                                        returns_days_to_close=days_to_close)
                CreditIdeaCreditScenario.objects.create(scenario=scenario, credit_idea=credit_idea, is_hedge=True,
                                                        returns_estimated_closing_date=closing_date,
                                                        returns_days_to_close=days_to_close)

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
            # context = self.get_context_data()
            credit_idea_id = request.POST.get('credit_idea_id')
            master_data = json.loads(request.POST.get('master_data'))
            response = save_credit_idea_data(master_data, credit_idea_id)
        except Exception:
            response = 'failed'
        return HttpResponse(response)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        credit_idea_id = self.request.GET.get('credit_idea_id')
        if credit_idea_id:
            try:
                credit_idea_object = CreditIdea.objects.get(id=credit_idea_id)
                arb_tradegroup = credit_idea_object.arb_tradegroup

                credit_idea_scenarios = CreditIdeaScenario.objects.filter(credit_idea_id=credit_idea_id)
                base_scenario = credit_idea_scenarios.filter(scenario='Base Date').first()
                if base_scenario:
                    estimated_closing_date = base_scenario.estimated_closing_date
                    if isinstance(estimated_closing_date, (date, datetime)):
                        estimated_closing_date = estimated_closing_date.strftime('%m/%d/%Y')
                    base_rebate = convert_to_float_else_zero(base_scenario.rebate)
                    base_spread = convert_to_float_else_zero(base_scenario.spread)
                    base_days_to_close = base_scenario.days_to_close or 0
                else:
                    estimated_closing_date = ''
                    base_rebate = 0.00
                    base_spread = 0.00
                    base_days_to_close = 0

                credit_idea_details = CreditIdeaDetails.objects.get(credit_idea_id=credit_idea_id)
                arb_base_case = credit_idea_details.base_case_downside or 0.00
                deal_value = credit_idea_details.deal_value or 0.00
                arb_outlier = credit_idea_details.outlier_downside or 0.00
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

                credit_idea_creditdetails = CreditIdeaCreditDetails.objects.get(credit_idea_id=credit_idea_id)
                bond_ticker = credit_idea_creditdetails.bond_ticker
                face_value_of_bonds = convert_to_float_else_zero(credit_idea_creditdetails.face_value_of_bonds)
                bond_est_purchase_price = convert_to_float_else_zero(credit_idea_creditdetails.bond_est_purchase_price)
                bbg_est_daily_vol = convert_to_float_else_zero(credit_idea_creditdetails.bbg_est_daily_vol)
                bbg_actual_thirty_day = convert_to_float_else_zero(credit_idea_creditdetails.bbg_actual_thirty_day)
                credit_team_view = credit_idea_creditdetails.credit_team_view
                credit_team_view = int(credit_team_view) if credit_team_view else credit_team_view
                base_break_price = convert_to_float_else_zero(credit_idea_creditdetails.base_break_price)
                conservative_break_price = convert_to_float_else_zero(credit_idea_creditdetails.conservative_break_price)
                call_price = convert_to_float_else_zero(credit_idea_creditdetails.call_price)
                make_whole_price = convert_to_float_else_zero(credit_idea_creditdetails.make_whole_price)
                equity_claw_percent = convert_to_float_else_zero(credit_idea_creditdetails.equity_claw_percent)
                equity_claw_value = convert_to_float_else_zero(credit_idea_creditdetails.equity_claw_value)
                blend = convert_to_float_else_zero(credit_idea_creditdetails.blend)
                change_of_control = convert_to_float_else_zero(credit_idea_creditdetails.change_of_control)
                acq_credit = convert_to_float_else_zero(credit_idea_creditdetails.acq_credit)
                proposed_ratio = convert_to_float_else_zero(credit_idea_creditdetails.proposed_ratio)

                credit_idea_creditscenario = CreditIdeaCreditScenario.objects.filter(credit_idea_id=credit_idea_id)
                scenario_with_hedge = credit_idea_creditscenario.filter(is_hedge=True)
                scenario_without_hedge = credit_idea_creditscenario.filter(is_hedge=False)

            except CreditIdea.DoesNotExist:
                raise Http404('Credit Idea not available')
            except CreditIdeaDetails.DoesNotExist:
                arb_base_case = 0.00
                deal_value = 0.00
                arb_outlier = 0.00
                arb_base_case_downside_type = ''
                arb_outlier_downside_type = ''
                target_ticker = ''
                acq_ticker = ''
                cash_terms = 0.00
                share_terms = 0.00
                target_dividends = 0.00
                acq_dividends = 0.00
                acq_pb_rate = 0.00
                target_pb_rate = 0.00
                fund_assets = 0.00
                float_so_value = 0.00
                nav_pct_impact = 0.00
            except CreditIdeaCreditDetails.DoesNotExist:
                bond_ticker = ''
                face_value_of_bonds = 0.00
                bond_est_purchase_price = 0.00
                bbg_est_daily_vol = 0.00
                bbg_actual_thirty_day = 0.00
                credit_team_view = 1
                base_break_price = 0.00
                conservative_break_price = 0.00
                call_price = 0.00
                make_whole_price = 0.00
                equity_claw_percent = 0.00
                equity_claw_value = 0.00
                blend = 0.00
                change_of_control = 0.00
                acq_credit = 0.00
                proposed_ratio = 0.00

            try:
                api_host = bbgclient.bbgclient.get_next_available_host()
                bbg_target_ticker = target_ticker.upper() + ' EQUITY' if 'equity' not in target_ticker.lower() else target_ticker.upper()
                bbg_acq_ticker = acq_ticker.upper() + ' EQUITY' if 'equity' not in acq_ticker.lower() else acq_ticker.upper()
                bbg_fed_fund_index = 'FEDL01 INDEX'
                bond_ticker = 'QZ992868 Corp'
                tickers_live_price = [bbg_target_ticker, bbg_acq_ticker, bbg_fed_fund_index, bond_ticker]
                bbg_fields = ['PX_LAST', 'DVD_SH_LAST', 'SECURITY_NAME', 'COUPON', 'AMT_OUTSTANDING', 'BID', 'ASK']
                live_price = bbgclient.bbgclient.get_secid2field(tickers_live_price, 'tickers',
                                                                 bbg_fields, req_type='refdata', api_host=api_host)

                target_live_price, acq_last_price, fed_funds_last_price = 0, 0, 0
                target_ticker_price = live_price.get(bbg_target_ticker)
                if target_ticker_price:
                    px_last_value = target_ticker_price.get('PX_LAST')
                    target_live_price = px_last_value[0] if len(px_last_value) > 0 else 0.00
                    target_live_price = convert_to_float_else_zero(target_live_price)
                    dvd_last_value = target_ticker_price.get('DVD_SH_LAST')
                    tgt_dvd = dvd_last_value[0] if len(dvd_last_value) > 0 else 0.00
                    tgt_dvd = convert_to_float_else_zero(tgt_dvd)

                acq_ticker_price = live_price.get(bbg_acq_ticker)
                if acq_ticker_price:
                    px_last_value = acq_ticker_price.get('PX_LAST')
                    acq_last_price = px_last_value[0] if len(px_last_value) > 0 else 0.00
                    acq_last_price = convert_to_float_else_zero(acq_last_price)
                    dvd_last_value = target_ticker_price.get('DVD_SH_LAST')
                    acq_dvd = dvd_last_value[0] if len(dvd_last_value) > 0 else 0.00
                    acq_dvd = convert_to_float_else_zero(acq_dvd)

                fed_fund_price = live_price.get(bbg_fed_fund_index)
                if fed_fund_price:
                    px_last_value = fed_fund_price.get('PX_LAST')
                    fed_funds_last_price = px_last_value[0] if len(px_last_value) > 0 else 0.00
                    fed_funds_last_price = convert_to_float_else_zero(fed_funds_last_price)
                
                bond_ticker_price = live_price.get(bond_ticker)
                if bond_ticker_price:
                    bbg_security_name = bond_ticker_price.get('SECURITY_NAME')
                    bbg_security_name = bbg_security_name[0] if len(bbg_security_name) > 0 else ''
                    bbg_interest_rate = bond_ticker_price.get('COUPON')
                    bbg_interest_rate = convert_to_float_else_zero(bbg_interest_rate[0]) if len(bbg_interest_rate) > 0 else 0.00
                    bbg_issue_size = bond_ticker_price.get('AMT_OUTSTANDING')
                    bbg_issue_size = convert_to_float_else_zero(bbg_issue_size[0]) / 1000000 if len(bbg_issue_size) > 0 else 0.00
                    bbg_bid_price = bond_ticker_price.get('BID')
                    bbg_bid_price = convert_to_float_else_zero(bbg_bid_price[0]) if len(bbg_bid_price) > 0 else 0.00
                    bbg_ask_price = bond_ticker_price.get('BID')
                    bbg_ask_price = convert_to_float_else_zero(bbg_ask_price[0]) if len(bbg_ask_price) > 0 else 0.00
                    bbg_last_price = bond_ticker_price.get('BID')
                    bbg_last_price = convert_to_float_else_zero(bbg_last_price[0]) if len(bbg_last_price) > 0 else 0.00

                else:
                    bbg_security_name = ''
                    bbg_interest_rate = 0.00
                    bbg_issue_size = 0.00
                    bbg_bid_price = 0.00
                    bbg_ask_price = 0.00
                    bbg_last_price = 0.00

                equity_claw = convert_to_float_else_zero(100 + bbg_interest_rate * 100)
                if make_whole_price == 0:
                    blend = 0.00
                else:
                    blend = convert_to_float_else_zero(equity_claw * equity_claw_percent + (1 - equity_claw_percent) * make_whole_price)

                arb_spend = convert_to_float_else_zero(face_value_of_bonds * bond_est_purchase_price * 0.01)
                passive_phase_arb_data = [
                    {'id': 'arb_spend', 'key': 'Spend', 'value': convert_to_str_decimal(arb_spend, 0)},
                    {'id': 'face_value_of_bonds', 'key': 'Face Value of Bonds', 'value': convert_to_str_decimal(face_value_of_bonds, 0)},
                ]
                
                potential_outcomes_data = [
                    {'id': 'base_break_price', 'key': 'Base Break Price', 'type_input': 'false', 'type': '', 'value': convert_to_str_decimal(base_break_price, 3)},
                    {'id': 'conservative_break_price', 'key': 'Conservative Break Price', 'type_input': 'false', 'type': '', 'value': convert_to_str_decimal(conservative_break_price, 3)},
                    {'id': 'call_price', 'key': 'Call Price', 'type_input': 'false', 'type': '', 'value': convert_to_str_decimal(call_price, 3)},
                    {'id': 'make_whole_price', 'key': 'Make-Whole Price', 'type_input': 'false', 'type': '', 'value': convert_to_str_decimal(make_whole_price, 3)},
                    {'id': 'equity_claw_value', 'key': 'Equity Claw', 'type_input': 'true', 'type': equity_claw_percent, 'value': convert_to_str_decimal(equity_claw, 3)},
                    {'id': 'blend', 'key': 'Blend', 'type_input': 'false', 'type': '', 'value': convert_to_str_decimal(blend, 3)},
                    {'id': 'change_of_control', 'key': 'Change of Control', 'type_input': 'false', 'type': '', 'value': convert_to_str_decimal(change_of_control, 3)},
                    {'id': 'acq_credit', 'key': str(acq_ticker) + ' Credit', 'type_input': 'false', 'type': '', 'value': convert_to_str_decimal(acq_credit, 3)},
                ]
                
                estimated_liquidity_data = [
                    {'id': 'bbg_est_daily_vol', 'key': 'BBG Est. Daily Vol. ($)', 'value': convert_to_str_decimal(bbg_est_daily_vol)},
                    {'id': 'bbg_actual_thirty_day', 'key': 'BBG Actual 30-day ($)', 'value': convert_to_str_decimal(bbg_actual_thirty_day)},
                    {'id': 'credit_team_view', 'key': 'Credit Team View', 'value': credit_team_view},
                ]
                
                bond_information_data = [
                    {'id': 'bbg_security_name', 'key': 'Security', 'value': bbg_security_name},
                    {'id': 'bond_ticker', 'key': 'Bond Ticker', 'value': bond_ticker},
                    {'id': 'bbg_interest_rate', 'key': 'Interest Rate (%)', 'value': convert_to_str_decimal(bbg_interest_rate, 3)},
                    {'id': 'bbg_issue_size', 'key': 'Issue Size ($)', 'value': convert_to_str_decimal(bbg_issue_size)},
                ]

                bond_price_data = [
                    {'id': 'est_purchase_price', 'key': 'Est. Purchased Price', 'value': convert_to_str_decimal(bond_est_purchase_price, 3)},
                    {'id': 'bbg_bid_price', 'key': 'Bid Price', 'value': convert_to_str_decimal(bbg_bid_price, 3)},
                    {'id': 'bbg_ask_price', 'key': 'Ask Price', 'value': convert_to_str_decimal(bbg_ask_price, 3)},
                    {'id': 'bbg_last_price', 'key': 'Last Price', 'value': convert_to_str_decimal(bbg_last_price, 3)},
                ]

                hedge_in_dollars = arb_spend * proposed_ratio * 0.01
                if target_live_price != 0:
                    shares_target_shorts = hedge_in_dollars / target_live_price
                else:
                    shares_target_shorts = 0.00
                acq_rebate_pct = fed_funds_last_price - acq_pb_rate
                target_rebate_pct = fed_funds_last_price - target_pb_rate
                less_short_rebate = target_live_price * -1 * target_rebate_pct * base_days_to_close / 365 * 0.01
                short_spread = base_spread + base_rebate + less_short_rebate
                hedging_data = [
                    {'id': 'proposed_ratio', 'key': 'Proposed Ratio', 'value': convert_to_str_decimal(proposed_ratio)},
                    {'id': 'hedge', 'key': 'Hedge in $', 'value': convert_to_str_decimal(hedge_in_dollars, 0)},
                    {'id': 'target_short', 'key': 'Shares of Target Short', 'value': convert_to_str_decimal(shares_target_shorts, 0)},
                    {'id': 'arb_spread', 'key': 'Arb Spread', 'value': convert_to_str_decimal(base_spread)},
                    {'id': 'less_rebate', 'key': 'Less:  Rebate', 'value': convert_to_str_decimal(base_rebate * -1)},
                    {'id': 'less_short_rebate', 'key': 'Less:  Short Rebate', 'value': convert_to_str_decimal(less_short_rebate)},
                    {'id': 'short_spread', 'key': 'Short Spread', 'value': convert_to_str_decimal(short_spread)},
                ]

                acquirer_30_premium = (1 + (ACQUIRER_PREMIUM * 0.01)) * acq_last_price
                topping_break_spread = ((acquirer_30_premium * share_terms) + cash_terms) - arb_base_case
                downsides_data = [
                    {'id': 'upside', 'key': 'Topping Bid Upside', 'type': 'Deal Value', 'value': round(deal_value, 2)},
                    {'id': 'base_downside', 'key': 'Base Case Downside', 'type': arb_base_case_downside_type, 'value': round(arb_base_case, 2)},
                    {'id': 'outlier_downside', 'key': 'Outlier Downside', 'type': arb_outlier_downside_type, 'value': round(arb_outlier, 2)},
                    {'id': 'thirty_premium', 'key': 'Acquirer 30% Premium', 'type': str(ACQUIRER_PREMIUM) + ' %', 'value': round(acquirer_30_premium, 2)},
                    {'id': 'normal_spread', 'key': 'Normal Break Spread', 'type': 'Break Spread', 'value': round(target_live_price - arb_base_case, 2)},
                    {'id': 'topping_spread', 'key': 'Topping Break Spread', 'type': 'Break Spread', 'value': round(topping_break_spread, 2)}
                ]
                gross_spread = convert_to_float_else_zero(deal_value) - convert_to_float_else_zero(target_live_price)
                dvd_adjusted_spread = gross_spread + target_dividends
                target_live_price = round(target_live_price, 2)
                dvd_adjusted_spread = convert_to_float_else_zero(gross_spread + target_dividends - acq_dividends * share_terms)
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
                
                rebate_data = [
                    {'id': 'funds_rate', 'type_input': 'true', 'key': 'Fed Funds Rate', 'acq_value': round(fed_funds_last_price, 2),
                     'target_value': round(fed_funds_last_price, 2)},
                    {'id': 'pb_rate', 'type_input': 'true', 'key': 'Less: PB Rate', 'acq_value': acq_pb_rate, 'target_value': target_pb_rate},
                    {'id': 'rebate_pct', 'type_input': 'false', 'key': 'Rebate %',
                     'acq_value': convert_to_str_decimal(acq_rebate_pct), 'target_value': convert_to_str_decimal(target_rebate_pct)},
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
                    temp_dict['implied_prob'] = round(convert_to_float_else_zero(1 - (gross_spread / topping_break_spread)) * 100, 2)
                    temp_dict['dollars_to_lose'] = round(convert_to_float_else_zero((gross_spread - topping_break_spread) * size_in_shares), 2)
                    temp_dict['DT_RowId'] = 'scenario_row_' + str(scenario_count)
                    scenario_data.append(temp_dict)
                    scenario_count += 1

                scenario_wo_hedge_data = []
                scenario_w_hedge_data = []
                keys = ['id', 'credit_idea_id', 'scenario', 'bond_last_price', 'bond_redemption', 'bond_carry_earned',
                        'bond_rebate', 'bond_hedge', 'bond_deal_value', 'bond_spread', 'returns_gross_pct',
                        'returns_annual_pct', 'returns_estimated_closing_date', 'returns_days_to_close',
                        'profits_principal', 'profits_carry', 'profits_rebate', 'profits_hedge', 'profits_total',
                        'profits_day_of_break']
                scenario_count = 1
                for scenario in scenario_without_hedge:
                    temp_dict = {key: getattr(scenario, key) for key in keys}
                    temp_dict['returns_estimated_closing_date'] = temp_dict['returns_estimated_closing_date'].strftime('%Y-%m-%d') if \
                        temp_dict['returns_estimated_closing_date'] else temp_dict['returns_estimated_closing_date']
                    temp_dict['database_id'] = temp_dict.get('id')
                    temp_dict['DT_RowId'] = 'scenario_wo_hedge_row_' + str(scenario_count)
                    scenario_wo_hedge_data.append(temp_dict)
                    scenario_count += 1

                scenario_count = 1
                for scenario in scenario_with_hedge:
                    temp_dict = {key: getattr(scenario, key) for key in keys}
                    temp_dict['returns_estimated_closing_date'] = temp_dict['returns_estimated_closing_date'].strftime('%Y-%m-%d') if \
                        temp_dict['returns_estimated_closing_date'] else temp_dict['returns_estimated_closing_date']
                    temp_dict['database_id'] = temp_dict.get('id')
                    temp_dict['DT_RowId'] = 'scenario_w_hedge_row_' + str(scenario_count)
                    scenario_w_hedge_data.append(temp_dict)
                    scenario_count += 1

            except Exception:
                downsides_data, spread_data, rebate_data, sizing_data = [], [], [], []
                scenario_data, passive_data, bond_price_data, bond_information_data = [], [], [], []
                estimated_liquidity_data = []
            context.update({
                'arb_tradegroup': arb_tradegroup.upper(),
                'downsides_data': json.dumps(downsides_data),
                'spread_data': json.dumps(spread_data),
                'rebate_data': json.dumps(rebate_data),
                'sizing_data': json.dumps(sizing_data),
                'scenario_data': json.dumps(scenario_data),
                'passive_data': json.dumps(passive_data),
                'passive_phase_arb_data': json.dumps(passive_phase_arb_data),
                'bond_price_data': json.dumps(bond_price_data),
                'bond_information_data': json.dumps(bond_information_data),
                'estimated_liquidity_data': json.dumps(estimated_liquidity_data),
                'potential_outcomes_data': json.dumps(potential_outcomes_data),
                'hedging_data': json.dumps(hedging_data),
                'scenario_wo_hedge_data': json.dumps(scenario_wo_hedge_data),
                'scenario_w_hedge_data': json.dumps(scenario_w_hedge_data),
            })
        return context


def save_credit_idea_data(master_data, credit_idea_id):
    response = 'failed'
    for key in master_data:
        if 'equity_scenario_data' in key.lower():
            scenario_data = master_data.get('equity_scenario_data')
            credit_idea_scenarios = CreditIdeaScenario.objects.filter(credit_idea_id=credit_idea_id)
            for data in scenario_data:
                try:
                    credit_idea_scenario = credit_idea_scenarios.get(id=data.get('database_id'),
                                                                     credit_idea_id=credit_idea_id)
                except CreditIdeaScenario.DoesNotExist:
                    credit_idea_scenario = CreditIdeaScenario(credit_idea_id=credit_idea_id)
                credit_idea_scenario.scenario = data.get('scenario')
                credit_idea_scenario.last_price = data.get('last_price') or 0.00
                credit_idea_scenario.dividends = data.get('dividends') or 0.00
                credit_idea_scenario.rebate = data.get('rebate') or 0.00
                credit_idea_scenario.hedge = data.get('hedge') or 0.00
                credit_idea_scenario.deal_value = data.get('deal_value') or 0.00
                credit_idea_scenario.spread = data.get('spread') or 0.00
                credit_idea_scenario.gross_pct = data.get('gross_pct') or 0.00
                credit_idea_scenario.annual_pct = data.get('annual_pct') or 0.00
                credit_idea_scenario.days_to_close = data.get('days_to_close') or 0.00
                credit_idea_scenario.dollars_to_make = data.get('dollars_to_make') or 0.00
                credit_idea_scenario.dollars_to_lose = data.get('dollars_to_lose') or 0.00
                credit_idea_scenario.implied_prob = data.get('implied_prob') or 0.00
                credit_idea_scenario.estimated_closing_date = data.get('exp_close')
                credit_idea_scenario.save()
        elif 'equity_details' in key.lower():
            try:
                credit_idea_details_object = CreditIdeaDetails.objects.get(credit_idea_id=credit_idea_id)
                credit_idea_details = master_data.get('equity_details')
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
                return 'failed'

        elif 'credit_details' in key.lower():
            try:
                credit_details_obj = CreditIdeaCreditDetails.objects.get(credit_idea_id=credit_idea_id)
                credit_details = master_data.get('credit_details')
                credit_details_obj.bond_ticker = credit_details.get('bond_information_bond_ticker')
                credit_details_obj.face_value_of_bonds = credit_details.get('bond_information_face_value_of_bonds')
                credit_details_obj.bbg_security_name = credit_details.get('bond_information_bbg_security_name')
                credit_details_obj.bbg_interest_rate = credit_details.get('bond_information_bbg_interest_rate')
                credit_details_obj.bbg_issue_size = credit_details.get('bond_information_bbg_issue_size')
                credit_details_obj.bond_est_purchase_price = credit_details.get('bond_price_est_purchase_price')
                credit_details_obj.bbg_bid_price = credit_details.get('bond_price_bbg_bid_price')
                credit_details_obj.bbg_ask_price = credit_details.get('bond_price_bbg_ask_price')
                credit_details_obj.bbg_last_price = credit_details.get('bond_price_bbg_last_price')
                credit_details_obj.base_break_price = credit_details.get('getpotential_outcomes_value_base_break_price')
                credit_details_obj.conservative_break_price = credit_details.get('potential_outcomes_value_conservative_break_price')
                credit_details_obj.call_price = credit_details.get('potential_outcomes_value_call_price')
                credit_details_obj.make_whole_price = credit_details.get('potential_outcomes_value_make_whole_price')
                credit_details_obj.equity_claw_percent = credit_details.get('potential_outcomes_equity_claw_value')
                credit_details_obj.equity_claw_value = credit_details.get('potential_outcomes_value_equity_claw_value')
                credit_details_obj.blend = credit_details.get('potential_outcomes_value_blend')
                credit_details_obj.change_of_control = credit_details.get('potential_outcomes_value_change_of_control')
                credit_details_obj.acq_credit = credit_details.get('potential_outcomes_value_acq_credit')
                credit_details_obj.proposed_ratio = credit_details.get('hedging_proposed_ratio')
                credit_details_obj.bbg_est_daily_vol = credit_details.get('estimated_liquidity_bbg_est_daily_vol')
                credit_details_obj.bbg_actual_thirty_day = credit_details.get('estimated_liquidity_bbg_actual_thirty_day')
                credit_team_view = credit_details.get('estimated_liquidity_credit_team_view') or 1
                credit_team_view = int(credit_team_view) if credit_team_view else 1
                credit_details_obj.credit_team_view = credit_team_view
                credit_details_obj.save()
            except CreditIdeaCreditDetails.DoesNotExist:
                return 'failed'
        elif 'credit_scenario_data' in key.lower():
            scenario_obj = CreditIdeaCreditScenario.objects.filter(credit_idea_id=credit_idea_id)
            scenario_data = master_data.get('credit_scenario_data')
            for data in scenario_data:
                try:
                    credit_idea_scenario = scenario_obj.get(id=data.get('database_id'), credit_idea_id=credit_idea_id)
                except CreditIdeaCreditScenario.DoesNotExist:
                    credit_idea_scenario = CreditIdeaCreditScenario(credit_idea_id=credit_idea_id)
                credit_idea_scenario.scenario = data.get('scenario')
                credit_idea_scenario.is_hedge = data.get('is_hedge')
                credit_idea_scenario.bond_last_price = data.get('bond_last_price') or 0.00
                credit_idea_scenario.bond_redemption = data.get('bond_redemption') or 0.00
                credit_idea_scenario.bond_carry_earned = data.get('bond_carry_earned') or 0.00
                credit_idea_scenario.bond_rebate = data.get('bond_rebate') or 0.00
                credit_idea_scenario.bond_hedge = data.get('bond_hedge') or 0.00
                credit_idea_scenario.bond_deal_value = data.get('bond_deal_value') or 0.00
                credit_idea_scenario.bond_spread = data.get('bond_spread') or 0.00
                credit_idea_scenario.returns_gross_pct = data.get('returns_gross_pct') or 0.00
                credit_idea_scenario.returns_annual_pct = data.get('returns_annual_pct') or 0.00
                credit_idea_scenario.returns_estimated_closing_date = data.get('returns_estimated_closing_date')
                credit_idea_scenario.returns_days_to_close = data.get('returns_days_to_close') or 0
                credit_idea_scenario.profits_principal = data.get('profits_principal') or 0.00
                credit_idea_scenario.profits_carry = data.get('profits_carry') or 0.00
                credit_idea_scenario.profits_rebate = data.get('profits_rebate') or 0.00
                credit_idea_scenario.profits_hedge = data.get('profits_hedge') or 0.00
                credit_idea_scenario.profits_total = data.get('profits_total') or 0.00
                credit_idea_scenario.profits_day_of_break = data.get('profits_day_of_break') or 0.00
                credit_idea_scenario.save()
    response = 'success'
    return response


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
            return 0.00
    else:
        return 0.00


def convert_to_str_decimal(value, decimal=2):
    try:
        if value:
            value = float(value)
            expression = '{:.' + str(decimal) + 'f}'
            return expression.format(value)
    except ValueError:
        return '0.00'
    return '0.00'
