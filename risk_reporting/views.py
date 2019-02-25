"""
Module contains Functions and Views to support Risk Reporting Functionality on the Portal
"""
import datetime
import pandas as pd
import numpy as np
import json
from django.shortcuts import render
from django.http import HttpResponse
from django.db import connection
from .models import ArbNAVImpacts, DailyNAVImpacts, FormulaeBasedDownsides
from django.conf import settings
# Following NAV Impacts Utilities


def calculate_pl_base_case(row):
    """ Calculates the PL Base Case based on Security Type """

    x = 0
    if row['SecType'] != 'EXCHOPT':
        return (row['PM_BASE_CASE'] * row['FxFactor'] * row['QTY']) - (row['CurrMktVal'] * row['FxFactor'])

    if row['PutCall'] == 'CALL':
        if row['StrikePrice'] <= row['PM_BASE_CASE']:
            x = (row['PM_BASE_CASE'] - row['StrikePrice']) * (row['QTY']) * row['FxFactor']
        else:
            x = 0
    elif row['PutCall'] == 'PUT':
        if row['StrikePrice'] >= row['PM_BASE_CASE']:
            x = (row['StrikePrice'] - row['PM_BASE_CASE']) * (row['QTY']) * row['FxFactor']
        else:
            x = 0
    return (-row['CurrMktVal'] * row['FxFactor']) + x


def calculate_base_case_nav_impact(row):
    """ Function to calculate Baase case NAV Impact. PL_BASE_CASE should be calculated first """
    return (row['PL_BASE_CASE'] / row['NAV']) * 100


def calculate_outlier_pl(row):
    """ Calculates Outlier PL or Outlier BASE_CASE """
    if row['SecType'] != 'EXCHOPT':
        return (row['Outlier'] * row['FxFactor'] * row['QTY']) - (row['CurrMktVal'] * row['FxFactor'])

    if row['PutCall'] == 'CALL':
        if row['StrikePrice'] <= row['Outlier']:
            x = (row['Outlier'] - row['StrikePrice']) * (row['QTY']) * row['FxFactor']
        else:
            x = 0
    elif row['PutCall'] == 'PUT':
        if row['StrikePrice'] >= row['Outlier']:
            x = (row['StrikePrice'] - row['Outlier']) * row['QTY'] * row['FxFactor']
        else:
            x = 0

    return (-row['CurrMktVal'] * row['FxFactor']) + x


def calculate_outlier_nav_impact(row):
    """ Calculates the Outlier NAV Impact based on OUTLIER_PL"""
    return (row['OUTLIER_PL'] / row['NAV']) * 100


# Create your views here.
def merger_arb_risk_attributes(request):
    """ View to Populate the Risk attributes for the Arbitrage Fund """

    # Populate all the deals
    nav_impacts_positions_df = pd.read_sql_query('SELECT * FROM test_wic_db.risk_reporting_arbnavimpacts', con=connection)

    # Convert Underlying Ticker to format Ticker Equity
    nav_impacts_positions_df['Underlying'] = nav_impacts_positions_df['Underlying'].apply(lambda x: x + " EQUITY" if "EQUITY" not in x else x)
    forumale_linked_downsides = pd.read_sql_query('SELECT * FROM test_wic_db.risk_reporting_formulaebaseddownsides',
                                                  con=connection)

    forumale_linked_downsides = forumale_linked_downsides[['TradeGroup', 'Underlying', 'base_case', 'outlier', 'LastUpdate']]
    merged_df = pd.merge(nav_impacts_positions_df, forumale_linked_downsides, how='inner',
                         on=['TradeGroup', 'Underlying'])

    merged_df.drop(columns=['PM_BASE_CASE', 'Outlier'], inplace=True)
    merged_df.rename(columns={'base_case': 'PM_BASE_CASE', 'outlier': 'Outlier'}, inplace=True)
    nav_impacts_positions_df = merged_df.copy()
    nav_impacts_positions_df = nav_impacts_positions_df[
        (nav_impacts_positions_df['PM_BASE_CASE'] != 'None') & (nav_impacts_positions_df['Outlier'] != 'None')]

    float_cols = ['DealTermsCash', 'DealTermsStock', 'DealValue', 'NetMktVal', 'FxFactor', 'Capital',
                  'BaseCaseNavImpact', 'RiskLimit',
                  'OutlierNavImpact', 'QTY', 'NAV', 'PM_BASE_CASE', 'Outlier', 'StrikePrice', 'LastPrice']

    nav_impacts_positions_df[float_cols] = nav_impacts_positions_df[float_cols].fillna(0).astype(float)
    nav_impacts_positions_df['CurrMktVal'] = nav_impacts_positions_df['QTY'] * nav_impacts_positions_df['LastPrice']
    # Calculate the Impacts

    nav_impacts_positions_df['PL_BASE_CASE'] = nav_impacts_positions_df.apply(calculate_pl_base_case, axis=1)
    nav_impacts_positions_df['BASE_CASE_NAV_IMPACT'] = nav_impacts_positions_df.apply(calculate_base_case_nav_impact,
                                                                                      axis=1)
    # Calculate Outlier Impacts
    nav_impacts_positions_df['OUTLIER_PL'] = nav_impacts_positions_df.apply(calculate_outlier_pl, axis=1)
    nav_impacts_positions_df['OUTLIER_NAV_IMPACT'] = nav_impacts_positions_df.apply(calculate_outlier_nav_impact,
                                                                                     axis=1)
    nav_impacts_positions_df = nav_impacts_positions_df.round({'BASE_CASE_NAV_IMPACT': 2, 'OUTLIER_NAV_IMPACT': 2})

    nav_impacts_sum_df = nav_impacts_positions_df.groupby(['TradeGroup', 'FundCode', 'RiskLimit', 'LastUpdate']).agg(
        {'BASE_CASE_NAV_IMPACT': 'sum', 'OUTLIER_NAV_IMPACT': 'sum'})

    nav_impacts_sum_df = pd.pivot_table(nav_impacts_sum_df, index=['TradeGroup', 'RiskLimit', 'LastUpdate'], columns='FundCode',
                                        aggfunc=np.sum,
                                        fill_value='')


    nav_impacts_sum_df.columns = ["_".join((i, j)) for i, j in nav_impacts_sum_df.columns]
    nav_impacts_sum_df.reset_index(inplace=True)

    settings.SQLALCHEMY_CONNECTION.execute('TRUNCATE TABLE test_wic_db.risk_reporting_dailynavimpacts')

    nav_impacts_sum_df.to_sql(con=settings.SQLALCHEMY_CONNECTION, if_exists='append', index=False, name='risk_reporting_dailynavimpacts',
                              schema='test_wic_db')

    impacts = DailyNAVImpacts.objects.all()
    if request.is_ajax():
        return_data = {'data': pd.DataFrame.from_records(impacts.values()).to_json(orient='records')}
        return HttpResponse(json.dumps(return_data), content_type='application/json')

    return render(request, 'risk_attributes.html', context={})

# The following should run in a scheduled job. Over here just get values from DB and render to the Front end...


def merger_arb_nav_impacts(request):
    """ Render the NAV Imacts on Merger Arb """
    # Get the Dataframe from models
    nav_impacts_positions_df = pd.DataFrame.from_records(ArbNAVImpacts.objects.all().values())
    nav_impacts_positions_df['CurrMktVal'] = nav_impacts_positions_df['QTY'] * nav_impacts_positions_df['LastPrice']
    float_cols = ['DealTermsCash', 'DealTermsStock', 'DealValue', 'NetMktVal', 'FxFactor', 'Capital',
                  'BaseCaseNavImpact', 'RiskLimit',
                  'OutlierNavImpact', 'QTY', 'NAV', 'PM_BASE_CASE', 'Outlier', 'StrikePrice', 'LastPrice']
    nav_impacts_positions_df[float_cols] = nav_impacts_positions_df[float_cols].astype(float)
    # Calculate the Impacts
    nav_impacts_positions_df['PL_BASE_CASE'] = nav_impacts_positions_df.apply(calculate_pl_base_case, axis=1)
    nav_impacts_positions_df['BASE_CASE_NAV_IMPACT'] = nav_impacts_positions_df.apply(calculate_base_case_nav_impact,
                                                                                      axis=1)
    # Calculate Outlier Impacts
    nav_impacts_positions_df['OUTLIER_PL'] = nav_impacts_positions_df.apply(calculate_outlier_pl, axis=1)
    nav_impacts_positions_df['OUTLIER_NAV_IMPACT'] = nav_impacts_positions_df.apply(calculate_outlier_nav_impact,
                                                                                    axis=1)
    nav_impacts_positions_df.rename(columns={'TG': 'TradeGroup'}, inplace=True) # Rename to TradeGroup
    # Sum Impacts of Individual Securities for Impacts @ TradeGroup level...
    nav_impacts_positions_df = nav_impacts_positions_df.round({'BASE_CASE_NAV_IMPACT': 2, 'OUTLIER_NAV_IMPACT': 2})
    nav_impacts_sum_df = nav_impacts_positions_df.groupby(['TradeGroup', 'FundCode', 'PM_BASE_CASE', 'RiskLimit']).agg(
        {'BASE_CASE_NAV_IMPACT': 'sum', 'OUTLIER_NAV_IMPACT': 'sum'})

    nav_impacts_sum_df = pd.pivot_table(nav_impacts_sum_df, index=['TradeGroup', 'RiskLimit'], columns='FundCode',
                                        fill_value='N/A')

    nav_impacts_sum_df.columns = ["_".join((i, j)) for i, j in nav_impacts_sum_df.columns]
    nav_impacts_sum_df.reset_index(inplace=True)

    nav_impacts_sum_df.to_sql(con=connection, if_exists='append', index=False, name='risk_reporting_dailynavimpacts',
                              schema='test_wic_db')
    return render(request, 'merger_arb_nav_impacts.html', context={'impacts':
                                                                   nav_impacts_sum_df.to_json(orient='index')})


def formula_based_downsides(request):
    """ This View should return the positions from FormulaDownside Models with ability to update
    the calulation fields for each deal at security level """
    # Gather data from Model and send to front end..Listen for any updates
    marb_positions = FormulaeBasedDownsides.objects.all()
    return render(request, 'downside_fomulae.html', context={'marb_positions': marb_positions})


def update_downside_formulae(request):
    """ View to Update the downside formulae for each position """
    # Only process POST requests
    response = 'Failed'
    if request.method == 'POST':
        # Gather the data
        try:
            id = request.POST['id']
            is_excluded = request.POST['is_excluded']
            risk_limit = request.POST['risk_limit']
            base_case_downside_type = request.POST['base_case_downside_type']
            base_case_reference_data_point = request.POST['base_case_reference_data_point']
            base_case_reference_price = request.POST['base_case_reference_price']
            base_case_operation = request.POST['base_case_operation']
            base_case_custom_input = request.POST['base_case_custom_input']
            base_case = request.POST['base_case']
            base_case_notes = request.POST['base_case_notes']
            cix_ticker = request.POST['cix_ticker']
            outlier_downside_type = request.POST['outlier_downside_type']
            outlier_reference_data_point = request.POST['outlier_reference_data_point']
            outlier_reference_price = request.POST['outlier_reference_price']
            outlier_operation = request.POST['outlier_operation']
            outlier_custom_input = request.POST['outlier_custom_input']
            outlier = request.POST['outlier']
            outlier_notes = request.POST['outlier_notes']

            FormulaeBasedDownsides.objects.update_or_create(id=id,
                                                            defaults={'IsExcluded': is_excluded,
                                                                      'RiskLimit': risk_limit,
                                                                      'BaseCaseDownsideType': base_case_downside_type,
                                                                      'BaseCaseReferenceDataPoint':
                                                                          base_case_reference_data_point,
                                                                      'cix_ticker':cix_ticker,
                                                                      'BaseCaseReferencePrice':
                                                                          base_case_reference_price,
                                                                      'BaseCaseOperation': base_case_operation,
                                                                      'BaseCaseCustomInput': base_case_custom_input,
                                                                      'base_case': base_case,
                                                                      'base_case_notes': base_case_notes,
                                                                      'OutlierDownsideType': outlier_downside_type,
                                                                      'OutlierReferenceDataPoint':
                                                                          outlier_reference_data_point,
                                                                      'OutlierReferencePrice': outlier_reference_price,
                                                                      'OutlierOperation': outlier_operation,
                                                                      'OutlierCustomInput': outlier_custom_input,
                                                                      'outlier': outlier,
                                                                      'outlier_notes': outlier_notes,
                                                                      'LastUpdate': datetime.datetime.now()})
            response = 'Success'
        except Exception as e:
            print(e)
            response = 'Failed'

    return HttpResponse(response)
