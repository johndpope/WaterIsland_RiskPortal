import datetime
import json
import numpy as np
import pandas as pd
import requests
from urllib.parse import urlencode
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import FormView, ListView
from django.urls import reverse
from django.db.models import Max
from .models import *
from portfolio_optimization.forms import EssDealTypeParametersForm


def ess_target_configs(request):
    # Render a response to View the current ESS configs.
    deal_type_parameters = EssDealTypeParameters.objects.all()
    normalized_sizing = NormalizedSizingByRiskAdjProb.objects.all()
    soft_catalyst_sizing = SoftCatalystNormalizedRiskSizing.objects.all()

    return render(request, 'ess_targets_configs.html', {'deal_type_paramters': deal_type_parameters,
                                                        'normalized_sizing': normalized_sizing,
                                                        'soft_catalyst_sizing': soft_catalyst_sizing
                                                        }
                  )


class EssDealTypeParametersView(FormView):
    template_name = "ess_targets_configs.html"
    form_class = EssDealTypeParametersForm
    success_url = '#'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        deal_type_parameters = EssDealTypeParameters.objects.all()
        normalized_sizing = NormalizedSizingByRiskAdjProb.objects.all()
        soft_catalyst_sizing = SoftCatalystNormalizedRiskSizing.objects.all()
        context.update({'deal_type_parameters': deal_type_parameters, 'normalized_sizing': normalized_sizing,
                        'soft_catalyst_sizing': soft_catalyst_sizing})
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        deal_type_id_to_edit = self.request.POST.get('deal_type_id')
        create_new_deal_type = not deal_type_id_to_edit
        if not create_new_deal_type:
            try:
                deal_type_obj = EssDealTypeParameters.objects.get(id=deal_type_id_to_edit)
                deal_type_obj.__dict__.update(data)
                deal_type_obj.save()
                create_new_deal_type = False
            except EssDealTypeParameters.DoesNotExist:
                create_new_deal_type = True
        if create_new_deal_type:
            if 'deal_type_id' in data.keys():
                data.pop('deal_type_id')
            EssDealTypeParameters.objects.create(**data)
        return super(EssDealTypeParametersView, self).form_valid(form)


def get_deal_type_details(request):
    """ Retreives all the details for the requested Deal Type """
    if request.method == 'POST':
        deal_type_id_to_edit = request.POST['deal_type_id_to_edit']
        deal_type_details = {}
        try:
            deal_type = EssDealTypeParameters.objects.get(id=deal_type_id_to_edit)
            deal_type_details['deal_type'] = deal_type.deal_type
            deal_type_details['long_probability'] = deal_type.long_probability
            deal_type_details['long_irr'] = deal_type.long_irr
            deal_type_details['long_max_risk'] = deal_type.long_max_risk
            deal_type_details['long_max_size'] = deal_type.long_max_size
            deal_type_details['short_probability'] = deal_type.short_probability
            deal_type_details['short_irr'] = deal_type.short_irr
            deal_type_details['short_max_risk'] = deal_type.short_max_risk
            deal_type_details['short_max_size'] = deal_type.short_max_size
        except EssDealTypeParameters.DoesNotExist:
            deal_type_details = []

    return JsonResponse({'deal_type_details': deal_type_details})


def delete_deal_type(request):
    response = None
    if request.method == 'POST':
        # Take the ID and Delete
        id_to_delete = request.POST['id']
        try:
            EssDealTypeParameters.objects.get(id=id_to_delete).delete()
            response = 'deal_type_deleted'
        except EssDealTypeParameters.DoesNotExist:
            response = 'deal_does_not_exist'

    return HttpResponse(response)


def update_soft_catalyst_risk_sizing(request):
    response = 'Failed'
    if request.method == 'POST':
        try:
            tier = request.POST['tier']
            win_probability = request.POST['win_probability']
            loss_probability = request.POST['loss_probability']
            max_risk = request.POST['max_risk']
            avg_position = request.POST['avg_position']

            SoftCatalystNormalizedRiskSizing.objects.filter(tier__contains=tier).delete()
            SoftCatalystNormalizedRiskSizing(tier=tier, win_probability=win_probability,
                                             loss_probability=loss_probability, max_risk=max_risk,
                                             avg_position=avg_position).save()
            response = 'Success'
        except Exception as e:
            print(e)

    return HttpResponse(response)


def update_normlized_sizing_by_risk_adj_prob(request):
    response = 'Failed'
    if request.method == 'POST':
        try:
            win_probability = request.POST['win_prob']
            loss_probability = request.POST['loss_prob']
            arb_max_risk = request.POST['arb_max_risk']
            risk_adj_loss = request.POST['risk_adj_loss']
            NormalizedSizingByRiskAdjProb.objects.all().delete()
            NormalizedSizingByRiskAdjProb(win_probability=win_probability, loss_probability=loss_probability,
                                          arb_max_risk=arb_max_risk, risk_adj_loss=risk_adj_loss).save()
            response = 'Success'
        except Exception as e:
            print(e)

    return HttpResponse(response)


class EssLongShortView(ListView):
    template_name = 'ess_potential_long_shorts.html'
    queryset = EssPotentialLongShorts.objects.all().order_by('-Date')
    context_object_name = 'esspotentiallongshorts_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        as_of = self.request.GET.get('as_of')
        if as_of:
            as_of = datetime.datetime.strptime(as_of, '%Y-%m-%d')
        else:
            as_of = EssPotentialLongShorts.objects.latest('Date').Date
        queryset = EssPotentialLongShorts.objects.filter(Date=as_of)
        context.update({'esspotentiallongshorts_list': queryset, 'as_of': as_of})
        return context


def ess_implied_probabilites(request):
    # Show Raw time-series of values of implied probabilities....
    field_names = []
    implied_probability_chart = {}
    ess_implied_prb_universe = EssUniverseImpliedProbability.objects.all()
    implied_probabilities_df = pd.DataFrame().from_records(ess_implied_prb_universe.
                                                           values('Date', 'deal_type', 'implied_probability'))

    # Get SPX Index Returnns
    start_date = implied_probabilities_df['Date'].min().strftime('%Y%m%d')
    end_date = implied_probabilities_df['Date'].max().strftime('%Y%m%d')

    r = requests.get("http://192.168.0.15:8080/wic/api/v1.0/general_histdata",
                     params={'idtype': "tickers", "fields": "PX_LAST",
                             "tickers": "SPX INDEX",
                             "override": "", "start_date": start_date, "end_date": end_date},
                     timeout=15)  # Set a 15 secs Timeout
    results = r.json()['results']
    spx_prices = pd.DataFrame.from_dict(results[0]['SPX INDEX']['fields'])
    spx_prices['PX_LAST'] = spx_prices['PX_LAST'].astype(float)
    spx_prices['implied_probability'] = ((spx_prices['PX_LAST'] / spx_prices['PX_LAST'].shift(
        1)) - 1.0) * 100  # daily change
    spx_prices['implied_probability'] = spx_prices['implied_probability'].cumsum()
    spx_prices['implied_probability'].fillna(0, inplace=True)
    spx_prices['deal_type'] = "SPX INDEX Ret(%)"
    del spx_prices['PX_LAST']
    spx_prices.rename(columns={'date': 'Date'}, inplace=True)

    implied_probabilities_df = pd.concat([implied_probabilities_df, spx_prices])
    if not implied_probabilities_df.empty:
        field_names = list(implied_probabilities_df['deal_type'].unique())
        implied_probabilities_df['implied_probability'] = implied_probabilities_df['implied_probability']. \
            apply(lambda x: np.round(x, decimals=2))

        implied_probabilities_df['Date'] = implied_probabilities_df['Date'].astype(str)
        implied_probabilities_df = implied_probabilities_df.pivot_table(columns=['deal_type'], index='Date'). \
            reset_index()

        implied_probabilities_df.columns = ["".join(('', j)) for i, j in implied_probabilities_df.columns]
        implied_probabilities_df.columns.values[0] = 'Date'
        implied_probabilities_df.reset_index(inplace=True)
        implied_probability_chart = implied_probabilities_df.to_json(orient='records')

    return render(request, 'implied_probability_track.html', {'implied_probability_chart': implied_probability_chart,
                                                              'field_names': json.dumps(field_names),
                                                              'ess_implied_prob': ess_implied_prb_universe})


def ess_implied_prob_drilldown(request):
    return_data = None
    if request.method == 'POST':
        try:
            date = request.POST['date']
            deal_type = request.POST['deal_type']
            date_adj = None
            if date == datetime.datetime.now().strftime('%Y-%m-%d'):
                date_adj = '(SELECT MAX(flat_file_as_of) from wic.daily_flat_file_db)'
            else:
                date_adj = "'" + date + "'"
            query = "SELECT DISTINCT flat_file_as_of as `Date`, TradeGroup, Fund, Ticker,Price, LongShort, SecType, " \
                    "DealUpside, DealDownside FROM wic.daily_flat_file_db WHERE Flat_file_as_of = " + date_adj + " AND " \
                                                                                                                 "Fund IN ('AED', 'TAQ') and AlphaHedge = 'Alpha' AND LongShort IN ('Long', 'Short') " \
                                                                                                                 "AND SecType = 'EQ' AND Sleeve = 'Equity Special Situations' and amount <> 0;"
            filtered_df = pd.read_sql_query(query, con=connection)
            return_data = get_implied_prob_df(filtered_df, date, deal_type)

        except Exception as e:
            print(e)
            return_data = None

    return JsonResponse({'data': return_data})


def get_implied_prob_df(imp_prob_tracker_df, date, deal_type, get_df=False):
    if deal_type in ['AED Long', 'AED Short', 'TAQ Long', 'TAQ Short']:

        if 'Long' in deal_type:
            imp_prob_tracker_df = imp_prob_tracker_df[imp_prob_tracker_df['LongShort'] == 'Long']
        else:
            imp_prob_tracker_df = imp_prob_tracker_df[imp_prob_tracker_df['LongShort'] == 'Short']

        # Slice for the Fund
        fund_code = deal_type.split(' ')[0]
        imp_prob_tracker_df = imp_prob_tracker_df[imp_prob_tracker_df['Fund'] == fund_code]

        imp_prob_tracker_df['implied_probability'] = 1e2 * (imp_prob_tracker_df['Price'] -
                                                            imp_prob_tracker_df['DealDownside']) / \
                                                     (imp_prob_tracker_df['DealUpside'] -
                                                      imp_prob_tracker_df['DealDownside'])

        imp_prob_tracker_df.replace([np.inf, -np.inf], np.nan, inplace=True)  # Replace Inf values

        imp_prob_tracker_df['Date'] = imp_prob_tracker_df['Date'].astype(str)

        imp_prob_tracker_df = imp_prob_tracker_df[['Date', 'Ticker', 'Price', 'TradeGroup',
                                                   'implied_probability']]

        # For Funds, provide a link to the TradeGroup story
        imp_prob_tracker_df['idea_link'] = imp_prob_tracker_df.apply(lambda x:
                                                                     "<td><a href='../position_stats/"
                                                                     "get_tradegroup_story?" +
                                                                     urlencode({'TradeGroup': x['TradeGroup'],
                                                                                'Fund': fund_code}) +
                                                                     "' target='_blank'>Story</a></td>",
                                                                     axis=1)
        imp_prob_tracker_df.columns = ['Date', 'alpha_ticker', 'price', 'deal_type', 'implied_probability',
                                       'idea_link']
        imp_prob_tracker_df['implied_probability'] = imp_prob_tracker_df['implied_probability'].round(2)
        if get_df:
            return imp_prob_tracker_df
        return imp_prob_tracker_df.to_json(orient='records')
    else:
        # Gather Data from Potential Long short timeseries..
        if deal_type == 'ESS IDEA Universe':
            implied_drilldowwn = pd.DataFrame.from_records(EssPotentialLongShorts.objects.all().filter(
                Date=date).values('Date', 'alpha_ticker', 'price', 'deal_type', 'implied_probability',
                                  'ess_idea_id'))

        elif deal_type == 'Universe (Long)':
            implied_drilldowwn = pd.DataFrame.from_records(EssPotentialLongShorts.objects.all().filter(
                Date=date, potential_long='Y').values('Date', 'alpha_ticker', 'price', 'deal_type',
                                                      'implied_probability', 'ess_idea_id'))

        elif deal_type == 'Universe (Short)':
            implied_drilldowwn = pd.DataFrame.from_records(EssPotentialLongShorts.objects.all().filter(
                Date=date, potential_short='Y').values('Date', 'alpha_ticker', 'price', 'deal_type',
                                                       'implied_probability', 'ess_idea_id'))

        elif deal_type == 'Universe (Unclassified)':
            implied_drilldowwn = pd.DataFrame.from_records(EssPotentialLongShorts.objects.all().filter(
                Date=date, potential_short='').values('Date', 'alpha_ticker', 'price', 'deal_type',
                                                      'implied_probability', 'ess_idea_id'))

        elif deal_type == 'Soft Universe Imp. Prob':
            implied_drilldowwn = pd.DataFrame.from_records(EssPotentialLongShorts.objects.all().filter(
                Date=date, catalyst='Soft').values('Date', 'alpha_ticker', 'price', 'deal_type',
                                                   'implied_probability', 'ess_idea_id'))

        elif deal_type in ['Hard-1', 'Hard-2', 'Hard-3', 'Soft-1', 'Soft-2', 'Soft-3']:
            cat = deal_type.split('-')[0]
            catalyst_tier = deal_type.split('-')[1]
            implied_drilldowwn = pd.DataFrame.from_records(EssPotentialLongShorts.objects.all().filter(
                Date=date, catalyst=cat, catalyst_tier=catalyst_tier).values('Date', 'alpha_ticker', 'price',
                                                                             'deal_type', 'implied_probability',
                                                                             'ess_idea_id'))

        else:
            implied_drilldowwn = pd.DataFrame.from_records(EssPotentialLongShorts.objects.all().filter(
                Date=date, deal_type=deal_type).values('Date', 'alpha_ticker', 'price', 'deal_type',
                                                       'implied_probability', 'ess_idea_id'))
        if not implied_drilldowwn.empty:
            implied_drilldowwn['implied_probability'] = implied_drilldowwn['implied_probability'].round(2)
            implied_drilldowwn['Date'] = implied_drilldowwn['Date'].astype(str)

        implied_drilldowwn['idea_link'] = implied_drilldowwn['ess_idea_id'].apply(
            lambda x: "<td><a href='" + reverse('risk:show_ess_idea') + "?ess_idea_id=" + str(x) +
                      "' target='_blank'>Open IDEA</a></td>")

        if get_df:
            return implied_drilldowwn
        return implied_drilldowwn.to_json(orient='records')


class MergerArbRorView(ListView):
    template_name = 'merger_arb_ror.html'
    queryset = ArbOptimizationUniverse.objects.all().order_by('-Date')
    context_object_name = 'arboptimizationuniverse_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        as_of = self.request.GET.get('as_of')
        if as_of:
            as_of = datetime.datetime.strptime(as_of, '%Y-%m-%d')
        else:
            as_of = ArbOptimizationUniverse.objects.latest('date_updated').date_updated
        queryset = ArbOptimizationUniverse.objects.filter(date_updated=as_of)
        context.update({'arboptimizationuniverse_list': queryset, 'as_of': as_of})
        return context


class ArbHardOptimizationView(ListView):
    template_name = 'arb_hard_optimization.html'
    queryset = HardFloatOptimization.objects.filter(date_updated=Max('date_updated'))
    context_object_name = 'hard_optimization_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        as_of = self.request.GET.get('as_of')
        if as_of:
            as_of = datetime.datetime.strptime(as_of, '%Y-%m-%d')
        else:
            as_of = HardFloatOptimization.objects.latest('date_updated').date_updated
        queryset = HardFloatOptimization.objects.filter(date_updated=as_of)
        context.update({'hard_optimization_list': queryset, 'as_of': as_of})
        return context


def save_hard_opt_comment(request):
    response = 'Failed'
    if request.method == 'POST':
        try:
            id = request.POST['id']
            note = request.POST['note']
            # get the Object
            deal_object = HardFloatOptimization.objects.get(id=id)
            deal_object.notes = note
            deal_object.save()
            response = 'Success'
        except Exception as e:
            print(e)

    return HttpResponse(response)
