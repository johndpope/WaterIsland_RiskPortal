import datetime
import pandas as pd
import numpy as np
import json
import bbgclient
from django.shortcuts import render
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.views.generic import FormView
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


def ess_potential_long_shorts(request):
    all_deals = EssPotentialLongShorts.objects.all()
    return render(request, 'ess_potential_long_shorts.html', {'all_deals': all_deals})


def ess_implied_probabilites(request):
    # Show Raw time-series of values of implied probabilities....
    field_names = []
    implied_probability_chart = {}
    ess_implied_prb_universe = EssUniverseImpliedProbability.objects.all()
    implied_probabilities_df = pd.DataFrame().from_records(ess_implied_prb_universe.
                                                           values('Date', 'deal_type', 'implied_probability'))

    if not implied_probabilities_df.empty:
        field_names = list(implied_probabilities_df['deal_type'].unique())
        implied_probabilities_df['implied_probability'] = implied_probabilities_df['implied_probability'].\
            apply(lambda x: np.round(x, decimals=2))

        implied_probabilities_df['Date'] = implied_probabilities_df['Date'].astype(str)
        implied_probabilities_df = implied_probabilities_df.pivot_table(columns=['deal_type'], index='Date').reset_index()

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

            if deal_type in ['AED Long', 'AED Short', 'TAQ Long', 'TAQ Short']:
                if date == datetime.datetime.now().strftime('%Y-%m-%d'):
                    date_adj = '(SELECT MAX(flat_file_as_of) from wic.daily_flat_file_db)'
                else:
                    date_adj = "'"+date+"'"
                query = "SELECT DISTINCT flat_file_as_of as `Date`, TradeGroup, Fund, Ticker,Price, "\
                    "LongShort, SecType, DealUpside, DealDownside "\
                    "FROM wic.daily_flat_file_db  "\
                    "WHERE Flat_file_as_of = "+date_adj+" AND Fund  "\
                    "IN ('AED', 'TAQ') and AlphaHedge = 'Alpha' AND  "\
                    "LongShort IN ('Long', 'Short') AND SecType = 'EQ' "\
                    "AND Sleeve = 'Equity Special Situations' and amount<>0"\

                imp_prob_tracker_df = pd.read_sql_query(query, con=connection)

                if 'Long' in deal_type:
                    imp_prob_tracker_df = imp_prob_tracker_df[imp_prob_tracker_df['LongShort'] == 'Long']
                else:
                    imp_prob_tracker_df = imp_prob_tracker_df[imp_prob_tracker_df['LongShort'] == 'Short']

                # Slice for the Fund
                imp_prob_tracker_df = imp_prob_tracker_df[imp_prob_tracker_df['Fund'] == deal_type.split(' ')[0]]

                imp_prob_tracker_df['implied_probability'] = 1e2*(imp_prob_tracker_df['Price'] - imp_prob_tracker_df['DealDownside'])/(imp_prob_tracker_df['DealUpside'] - imp_prob_tracker_df['DealDownside'])

                imp_prob_tracker_df.replace([np.inf, -np.inf], np.nan, inplace=True)  # Replace Inf values

                imp_prob_tracker_df['Date'] = imp_prob_tracker_df['Date'].astype(str)

                imp_prob_tracker_df = imp_prob_tracker_df[['Date', 'Ticker', 'Price', 'TradeGroup', 'implied_probability']]
                imp_prob_tracker_df.columns = ['Date', 'alpha_ticker', 'price', 'deal_type', 'implied_probability']
                return_data = imp_prob_tracker_df.to_json(orient='records')

            else:
                # Gather Data from Potential Long short timeseries..
                if deal_type == 'ESS IDEA Universe':
                    implied_drilldowwn = pd.DataFrame.from_records(EssPotentialLongShorts.objects.all().filter(Date=date).values('Date', 'alpha_ticker', 'price',  'deal_type', 'implied_probability'))

                elif deal_type == 'Universe (Long)':
                    implied_drilldowwn = pd.DataFrame.from_records(EssPotentialLongShorts.objects.all().filter(Date=date, potential_long='Y').values('Date', 'alpha_ticker', 'price',  'deal_type', 'implied_probability'))

                elif deal_type == 'Universe (Short)':
                    implied_drilldowwn = pd.DataFrame.from_records(EssPotentialLongShorts.objects.all().filter(Date=date, potential_short='Y').values('Date', 'alpha_ticker', 'price',  'deal_type', 'implied_probability'))

                elif deal_type == 'Universe (Unclassified)':
                    implied_drilldowwn = pd.DataFrame.from_records(EssPotentialLongShorts.objects.all().filter(Date=date, potential_short='').values('Date', 'alpha_ticker',  'price', 'deal_type', 'implied_probability'))

                else:
                    implied_drilldowwn = pd.DataFrame.from_records(EssPotentialLongShorts.objects.all().filter(Date=date, deal_type=deal_type).values('Date', 'alpha_ticker', 'price', 'deal_type', 'implied_probability'))
                implied_drilldowwn['Date'] = implied_drilldowwn['Date'].astype(str)

                return_data = implied_drilldowwn.to_json(orient='records')

        except Exception as e:
            print(e)
            return_data = None

    return JsonResponse({'data': return_data})