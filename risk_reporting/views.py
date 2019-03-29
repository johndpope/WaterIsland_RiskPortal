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
from .models import ArbNAVImpacts, DailyNAVImpacts, FormulaeBasedDownsides, PositionLevelNAVImpacts
from django.conf import settings
from django_slack import slack_message
from django.db.models import Max
from django.db import close_old_connections

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
def deal_info_download(request):
    # DealInfo.csv @ the Deal Level
    deal_level = pd.DataFrame.from_records(FormulaeBasedDownsides.objects.filter(IsExcluded__contains='No',
                                                                                 RiskLimit__isnull=False)
                                           .values('TradeGroup', 'RiskLimit').distinct())

    deal_level.rename(columns={'RiskLimit': 'Risk Limit', 'TradeGroup': 'Deal'}, inplace=True)
    # Add extra columns
    deal_level['Analyst'] = ''
    deal_level['BBG Event ID'] = ''
    deal_level['Catalyst Rating'] = ''
    deal_level['Closing Date'] = ''
    deal_level['Deal Cash Terms'] = ''
    deal_level['Deal Downside'] = ''
    deal_level['Deal Stock Terms'] = ''
    deal_level['Deal Upside'] = ''
    deal_level['Expected Acquirer Dividends'] = ''
    deal_level['Expected Target Dividends'] = ''
    deal_level['Number of Acquirer Dividends'] = ''
    deal_level['Number of Target Dividends'] = ''
    deal_level['Strategy Type'] = ''
    deal_level['Tradegroup Bucket'] = ''
    deal_level['AED Weight'] = ''
    deal_level['ARB Weight'] = ''
    deal_level['CAM Weight'] = ''
    deal_level['LEV Weight'] = ''
    deal_level['LG Weight'] = ''
    deal_level['TACO Weight'] = ''
    deal_level['TAQ Weight'] = ''
    deal_level['WED Weight'] = ''
    deal_level['WIC Weight'] = ''
    deal_level['MACO Weight'] = ''
    deal_level['MALT Weight'] = ''
    deal_level['Catalyst Type'] = ''

    deal_level = deal_level[['Deal', 'Analyst', 'BBG Event ID', 'Catalyst Rating', 'Closing Date', 'Deal Cash Terms',
                             'Deal Downside', 'Deal Stock Terms', 'Deal Upside', 'Expected Acquirer Dividends',
                             'Expected Target Dividends', 'Number of Acquirer Dividends', 'Number of Target Dividends',
                             'Risk Limit', 'Strategy Type', 'Tradegroup Bucket', 'AED Weight', 'ARB Weight',
                             'CAM Weight',
                             'LEV Weight', 'LG Weight', 'TACO Weight', 'TAQ Weight', 'WED Weight', 'WIC Weight',
                             'MACO Weight', 'MALT Weight', 'Catalyst Type']]

    # Add % sign to Risk Limit
    deal_level['Risk Limit'] = deal_level['Risk Limit'].apply(lambda x: str(x) + "%")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=DealInfo.csv'
    deal_level.to_csv(path_or_buf=response, index=False)

    return response



def security_info_download(request):
    # Get the Deal Level and Security Level files in the required format.
    position_level = pd.DataFrame.from_records(
        FormulaeBasedDownsides.objects.filter(IsExcluded__contains='No', base_case__isnull=False,
                                              outlier__isnull=False).
        values('TradeGroup', 'Underlying', 'outlier', 'base_case'))
    # Rename columns
    position_level.rename(columns={'TradeGroup': 'Deal', 'Underlying': 'Security', 'outlier': 'Outliers',
                                   'base_case': 'PM Base Case'}, inplace=True)

    position_level['Security'] = position_level['Security'].apply(lambda x: ' '.join(x.split(' ')[0:2]))
    # Add the other required columns
    position_level['Alternate Ticker'] = ''
    position_level['Rebate Rate'] = ''
    position_level['Price'] = ''
    position_level['Adj_CR_01'] = ''
    position_level['CR_01'] = ''
    position_level['DV01'] = ''
    position_level['Beta'] = ''

    # Rearrange columns
    position_level = position_level[['Deal', 'Security', 'Alternate Ticker', 'Outliers', 'PM Base Case', 'Rebate Rate',
                                     'Price', 'Adj_CR_01', 'CR_01', 'DV01', 'Beta']]
    # This should be named SecurityInfo.csv
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=SecurityInfo.csv'
    position_level.to_csv(path_or_buf=response, index=False)
    return response


def merger_arb_risk_attributes(request):
    """ View to Populate the Risk attributes for the Arbitrage Fund """
    close_old_connections()
    ytd_performances = pd.read_sql_query(
        'SELECT DISTINCT tradegroup, fund, pnl_bps FROM test_wic_db.realtime_pnl_impacts_arbitrageytdperformance',
        con=connection)
    ytd_performances.columns = ['TradeGroup', 'FundCode', 'PnL_BPS']

    forumale_linked_downsides = pd.read_sql_query('SELECT * FROM test_wic_db.risk_reporting_formulaebaseddownsides',
                                                  con=connection)

    forumale_linked_downsides = forumale_linked_downsides[['TradeGroup', 'Underlying', 'base_case', 'outlier',
                                                           'LastUpdate', 'LastPrice']]

    negative_pnl_accounted = True
    if len(ytd_performances) == 0:
        negative_pnl_accounted = False

    last_calculated_on = PositionLevelNAVImpacts.objects.latest('CALCULATED_ON').CALCULATED_ON

    impacts_df = pd.DataFrame.from_records(DailyNAVImpacts.objects.all().values())
    impacts_df['LastUpdate'] = None

    def get_last_update_downside(row):
        try:
            last_update = forumale_linked_downsides[forumale_linked_downsides['TradeGroup'] == row['TradeGroup']][
            'LastUpdate'].max()
        except:
            last_update = None
        return last_update

    impacts_df['LastUpdate'] = impacts_df.apply(get_last_update_downside, axis=1)

    nav_impacts_positions_df = pd.DataFrame.from_records(PositionLevelNAVImpacts.objects.all().values())

    ytd_performances = pd.pivot_table(ytd_performances, index=['TradeGroup'], columns=['FundCode'],
                                      aggfunc=np.sum,
                                      fill_value='')

    ytd_performances.columns = ["_".join((i, j)) for i, j in ytd_performances.columns]
    ytd_performances.reset_index(inplace=True)
    floats = ['TradeGroup', 'PnL_BPS_ARB', 'PnL_BPS_MACO', 'PnL_BPS_MALT', 'PnL_BPS_AED',
                                         'PnL_BPS_CAM', 'PnL_BPS_LG', 'PnL_BPS_LEV']
    ytd_performances = ytd_performances[floats].fillna(0)
    ytd_performances = ytd_performances.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)

    if request.is_ajax():
        return_data = {'data': impacts_df.to_json(orient='records'),
                       'positions': nav_impacts_positions_df.to_json(orient='records'),
                       'ytd_pnl': ytd_performances.to_json(orient='records')}
        return HttpResponse(json.dumps(return_data), content_type='application/json')

    return render(request, 'risk_attributes.html', context={'negative_pnl_accounted': negative_pnl_accounted,
                                                            'last_calculated_on': last_calculated_on})


# The following should run in a scheduled job. Over here just get values from DB and render to the Front end...


def formulae_downsides_new_deal_add(request):
    """ Add new deal to formulae based downsides page """
    response = 'Failed'
    if request.method == 'POST':
        # Get the Data
        tradegroup = request.POST['tradegroup']
        underlying_security = request.POST['underlying_security']
        analyst = request.POST['analyst']
        origination_date = request.POST['origination_date']
        deal_value = request.POST['deal_value']
        position_in_acquirer = request.POST['position_in_acquirer']
        acquirer_security = request.POST['acquirer_security']
        risk_limit = request.POST['risk_limit']

        # Get the max ID
        try:
            max_id = int(FormulaeBasedDownsides.objects.all().aggregate(Max('id'))['id__max'])
            insert_id = max_id + 1
            obj = FormulaeBasedDownsides()
            obj.id = insert_id
            obj.TradeGroup = tradegroup
            obj.Underlying = underlying_security
            obj.TargetAcquirer = 'Target'
            obj.Analyst = analyst
            obj.RiskLimit = risk_limit
            obj.OriginationDate = origination_date
            obj.DealValue = deal_value
            obj.save()

            # If Position in Acquirer is Yes then create another row
            if position_in_acquirer == 'Yes':
                obj2 = FormulaeBasedDownsides()
                obj2.id = insert_id + 1
                obj2.TradeGroup = tradegroup
                obj2.Underlying = acquirer_security
                obj2.TargetAcquirer = 'Acquirer'
                obj2.Analyst = analyst
                obj2.RiskLimit = risk_limit
                obj2.OriginationDate = origination_date
                obj2.DealValue = deal_value
                obj2.save()

            response = 'Success'

        except Exception as e:
            response = 'Failed'
            print(e)
    return HttpResponse(response)


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
    nav_impacts_positions_df.rename(columns={'TG': 'TradeGroup'}, inplace=True)  # Rename to TradeGroup
    # Sum Impacts of Individual Securities for Impacts @ TradeGroup level...
    nav_impacts_positions_df = nav_impacts_positions_df.round({'BASE_CASE_NAV_IMPACT': 2, 'OUTLIER_NAV_IMPACT': 2})
    nav_impacts_sum_df = nav_impacts_positions_df.groupby(['TradeGroup', 'FundCode', 'PM_BASE_CASE', 'RiskLimit']).agg(
        {'BASE_CASE_NAV_IMPACT': 'sum', 'OUTLIER_NAV_IMPACT': 'sum'})

    nav_impacts_sum_df = pd.pivot_table(nav_impacts_sum_df, index=['TradeGroup', 'RiskLimit'], columns='FundCode',
                                        fill_value='N/A')

    nav_impacts_sum_df.columns = ["_".join((i, j)) for i, j in nav_impacts_sum_df.columns]
    nav_impacts_sum_df.reset_index(inplace=True)

    nav_impacts_sum_df.to_sql(con=settings.SQLALCHEMY_CONNECTION, if_exists='append', index=False,
                              name='risk_reporting_dailynavimpacts',
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
            row_id = request.POST['id']
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

            if outlier_downside_type == 'None' or outlier_downside_type is None:
                # Outlier should match base case by Default
                outlier_downside_type = 'Matches Base Case'
                outlier_reference_data_point = base_case_reference_data_point
                outlier_reference_price = base_case_reference_price
                outlier_operation = base_case_operation
                outlier_custom_input = base_case_custom_input
                outlier = base_case

            # Retroactively update Risk Limit for all matching TradeGroups
            obj = FormulaeBasedDownsides.objects.get(id=row_id)
            deal_name = obj.TradeGroup
            matching_tradegroups = FormulaeBasedDownsides.objects.filter(TradeGroup__exact=deal_name)
            for deals in matching_tradegroups:
                deals.RiskLimit = risk_limit

            old_base_case_downside = obj.base_case
            old_outlier = obj.outlier
            old_risk_limit = obj.RiskLimit
            obj.IsExcluded = is_excluded
            obj.RiskLimit = risk_limit
            obj.BaseCaseDownsideType = base_case_downside_type
            obj.BaseCaseReferenceDataPoint = base_case_reference_data_point
            obj.cix_ticker = cix_ticker
            obj.BaseCaseReferencePrice = base_case_reference_price
            obj.BaseCaseOperation = base_case_operation
            obj.BaseCaseCustomInput = base_case_custom_input
            obj.base_case = base_case
            obj.base_case_notes = base_case_notes
            obj.OutlierDownsideType = outlier_downside_type
            obj.OutlierReferenceDataPoint = outlier_reference_data_point
            obj.OutlierReferencePrice = outlier_reference_price
            obj.OutlierOperation = outlier_operation
            obj.OutlierCustomInput = outlier_custom_input
            obj.outlier = outlier
            obj.outlier_notes = outlier_notes
            obj.LastUpdate = datetime.datetime.now()
            obj.save()
            response = 'Success'
            ip_addr = request.META['REMOTE_ADDR']
            slack_message('portal_downsides.slack',
                          {'updated_deal': str(obj.TradeGroup),
                           'underlying_security': obj.Underlying,
                           'risk_limit': str(old_risk_limit) + " -> " + str(obj.RiskLimit),
                           'base_case': str(old_base_case_downside) + " -> " + str(obj.base_case),
                           'outlier': str(old_outlier) + " -> " + str(obj.outlier),
                           'IP': str(ip_addr)},
                          channel='portal_downsides',
                          token=settings.SLACK_TOKEN,
                          name='PORTAL DOWNSIDE UPDATE AGENT')
        except Exception as e:
            print(e)
            response = 'Failed'

    return HttpResponse(response)
