import os
import datetime
import json
import ast
from dateutil.relativedelta import relativedelta
import numpy as np
import requests
import ess_premium_analysis
import ess_function
from django_pandas.io import read_frame
from django.db.models import Max
from wic_news.models import NewsMaster
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, Http404
from django.core import serializers
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from celery.result import AsyncResult
from risk.chart_utils import *
from notes.models import NotesMaster
from .tasks import add_new_idea
from .models import *


api_host = bbgclient.bbgclient.get_next_available_host()


# region Merger Arbitrage IDEA Database
@csrf_exempt
def retrieve_cix_index(request):
    response = 'Failed'
    if request.method == 'POST':
        # Get the parameters
        try:
            deal_id = request.POST['deal_id']
            cix_index = request.POST['cix']
            # Get the Deal Object
            deal_object = MA_Deals.objects.get(id=deal_id)
            deal_object.cix_index = cix_index
            # Fetch Historical CIX Price Chart...
            r_histdata = requests.get("http://" + api_host + "/wic/api/v1.0/general_histdata",
                                      params={'idtype': "tickers", "fields": "PX_LAST",
                                              "tickers": ','.join([cix_index]),
                                              "override": "",
                                              "start_date": (datetime.datetime.now() -
                                                             relativedelta(months=12))
                                                            .strftime('%Y%m%d'),
                                              "end_date": datetime.datetime.now()
                                                          .strftime('%Y%m%d')},
                                      timeout=15)  # Set a 15 secs Timeout
            hist_data_results = r_histdata.json()['results']
            px_last_historical = json.dumps(hist_data_results[0][cix_index]['fields'])
            deal_object.cix_index_chart = px_last_historical
            deal_object.save()
            response = deal_object.cix_index_chart
        except Exception as exception:
            print(exception)

    return HttpResponse(response)


def mna_idea_add_unaffected_date(request):
    response = 'Failed'
    if request.method == 'POST':
        try:
            # Get parameters
            deal_id = request.POST['deal_id']
            unaffected_date = request.POST['unaffected_date']
            deal_object = MA_Deals.objects.get(id=deal_id)
            deal_object.unaffected_date = unaffected_date
            deal_object.save()
            response = 'Success'
        except Exception as exception:
            print(exception)

    return HttpResponse(response)


def retrieve_spread_index(request):
    response = 'Failed'
    if request.method == 'POST':
        # Get the parameters
        try:
            deal_id = request.POST['deal_id']
            spread_index = request.POST['spread_index']
            # Get the Deal Object
            deal_object = MA_Deals.objects.get(id=deal_id)
            deal_object.spread_index = spread_index
            # Fetch Historical CIX Price Chart...
            r_histdata = requests.get("http://" + api_host + "/wic/api/v1.0/general_histdata",
                                      params={'idtype': "tickers", "fields": "PX_LAST",
                                              "tickers": ','.join([spread_index]),
                                              "override": "",
                                              "start_date": (datetime.datetime.now()
                                                             - relativedelta(months=12))
                                                            .strftime('%Y%m%d'),
                                              "end_date": datetime.datetime.now()
                                                          .strftime('%Y%m%d')},
                                      timeout=15)  # Set a 15 secs Timeout
            hist_data_results = r_histdata.json()['results']
            px_last_historical = json.dumps(hist_data_results[0][spread_index]['fields'])
            deal_object.spread_index_chart = px_last_historical
            deal_object.save()
            response = deal_object.spread_index_chart
        except Exception as exception:
            print(exception)

    return HttpResponse(response)


def calculate_mna_idea_deal_value(request):
    response = 'Failed'
    if request.method == 'POST':
        # Collect the parameters...
        try:
            acquirer_ticker = request.POST['acquirer_ticker']
            deal_cash_terms = float(request.POST['deal_cash_terms'])
            deal_stock_terms = float(request.POST['deal_stock_terms'])
            target_dividends = float(request.POST['target_dividends'])
            acquirer_dividends = float(request.POST['acquirer_dividends'])
            short_rebate = float(request.POST['short_rebate'])
            stub_cvr_value = float(request.POST['stub_cvr_value'])
            # Get latest acquirer price

            px_last = float(bbgclient.bbgclient.get_secid2field([acquirer_ticker], 'tickers',
                                                                ['CRNCY_ADJ_PX_LAST'],req_type='refdata',
                                                                api_host=api_host)[acquirer_ticker]
                            ['CRNCY_ADJ_PX_LAST'][0]) if deal_stock_terms > 0 else 0

            deal_value = (deal_cash_terms + (px_last * deal_stock_terms) + target_dividends -
                          acquirer_dividends + short_rebate + stub_cvr_value)

            response = str(deal_value)

        except Exception as exception:
            print(exception)
            response = 'Failed'
    return HttpResponse(response)


def delete_mna_idea(request):
    response = 'Failed'
    if request.method == 'POST':
        try:
            id = request.POST['id']
            MA_Deals.objects.get(id=id).delete()
            response = 'Success'
        except Exception as exception:
            print(exception)
            response = 'Failed'

    return HttpResponse(response)


def mna_idea_historical_downside_estimate(request):
    """
     View to Get an Object of Weekly downside Estimates from a given Start date and End Date
    :param request: Request object containing deal_id, start_date and end_date
    :return: Appropriate String response
    """

    response = 'Failed'
    if request.method == 'POST':
        try:
            # Only Process POST request
            start_date = request.POST['start_date']
            end_date = request.POST['end_date']
            deal_id = request.POST['deal_id']
            start_date = datetime.datetime.strptime(start_date, "%m/%d/%Y").strftime("%Y-%m-%d")
            end_date = datetime.datetime.strptime(end_date, "%m/%d/%Y").strftime("%Y-%m-%d")

            # Call ORM to get the object
            downside_estimate_object = MA_Deals_WeeklyDownsideEstimates.objects.filter(deal=deal_id,
                                                                                       start_date=start_date,
                                                                                       end_date=end_date)

            if not downside_estimate_object:
                response = 'Empty'
            else:
                response = serializers.serialize('json', downside_estimate_object)
        except Exception as exception:
            print(exception)
            response = 'Failed'

    return HttpResponse(response)


def get_start_end_dates(year, week):
    """
    Helper function to get start and end dates for a week
    :param year: Year
    :param week: Week Number
    :return: Start and End dates
    """
    d = datetime.date(year, 1, 1)
    if d.weekday() <= 3:
        d = d - datetime.timedelta(d.weekday())
    else:
        d = d + datetime.timedelta(7 - d.weekday())

    dlt = datetime.timedelta(days=(week - 1) * 7)

    return d + dlt, d + dlt + datetime.timedelta(days=6)


def add_or_update_mna_idea_weekly_downside_estimates(request):
    """
    @param request: Request Object containing downside_estimate, downside_analyst, downside_comment
    @return: Success or Error depending on the outcome of the execution...
    """
    # Check if request type is POST
    response = 'Failed'
    if request.method == 'POST':
        try:
            # Retrieve the parameters
            downside_estimate = request.POST['downside_estimate']
            downside_analyst = request.POST['downside_analyst']
            downside_comment = request.POST['downside_comment']
            deal_id = request.POST['deal_id']
            now = datetime.datetime.now()

            # Get the Current Week number from the timestamp and the start and end of the week for historical retrieval
            # Isocalendar returns a tuple with Year, Weeknumber and weekday in respective order...
            year, week_number = now.date().isocalendar()[0:2]
            # current week starts on Monday and ends the following Sunday...
            start_day, end_day = get_start_end_dates(year,
                                                     week_number)
            MA_Deals_WeeklyDownsideEstimates(week_no=week_number, start_date=start_day, end_date=end_day,
                                             deal_id=deal_id, analyst=downside_analyst, comment=downside_comment,
                                             estimate=downside_estimate, date_updated=datetime.datetime.now()).save()
            # Save the last Updated downside estimate
            deal_obj = MA_Deals.objects.get(id=deal_id)
            deal_obj.last_downside_update = datetime.datetime.now()
            deal_obj.save()
            response = 'Success'
        except Exception as exception:
            print(exception)  # Log this
            response = 'Failed'

    return HttpResponse(response)


def update_mna_idea_lawyer_report(request):
    """
    @param request: Request Object containing ID of the Report, Analyst, Report, Rating, Date
    @return: Success or Failed depending on the outcome of the execution.
    """
    response = 'Failed'
    if request.method == 'POST':
        try:
            id = request.POST['id']
            analyst_by = request.POST['analyst_by']
            analyst_rating = request.POST['analyst_rating']
            date = request.POST['date']
            report = request.POST['report']
            MA_Deals_Lawyer_Reports.objects.update_or_create(id=id,
                                                             defaults={'analyst_by': analyst_by,
                                                                       'lawyer_report_date': date,
                                                                       'lawyer_report': report,
                                                                       'analyst_rating': analyst_rating})
            response = 'Success'
        except Exception as exception:
            print(exception)    # Exceptions should be Logged...

    return HttpResponse(response)


def delete_mna_idea_lawyer_report(request):
    """
    @param request: Request object containing ID of the report to be deleted
    @return: Success or Failure status depending on the outcome of the execution
    """
    response = 'Failed'
    if request.method == 'POST':
        try:
            id_to_be_deleted = request.POST['id']
            MA_Deals_Lawyer_Reports.objects.get(id=id_to_be_deleted).delete()
            response = 'Success'
        except Exception as exception:
            print(exception)    #Exceptions should be Logged...

    return HttpResponse(response)


def add_new_mna_idea_lawyer_report(request):
    """
    :param request: Request Object containing the Lawyer Report Form
    :return: Success/Failure String depending on outcome of addition...
    """
    response = 'Failed'
    if request.method == 'POST':
        try:
            deal_id = request.POST['deal_id']
            lawyer_report_date = request.POST['lawyer_report_date']
            analyst_by = request.POST['analyst_by']
            lawyer_report = request.POST['lawyer_report']
            analyst_rating = request.POST['analyst_rating']
            lawyer_report_object = MA_Deals_Lawyer_Reports(deal_id=deal_id, lawyer_report_date=lawyer_report_date,
                                                           analyst_by=analyst_by, lawyer_report=lawyer_report,
                                                           analyst_rating=analyst_rating)
            lawyer_report_object.save()
            response = 'Success'

        except Exception as exception:
            print(exception)    # Exception should be logged..
            response = 'Failed'

    return HttpResponse(response)


def mna_idea_add_peers(request):
    """
        :param request: Request Object containing the Peers form
        :return: Success/Failure String depending on outcome of addition...
    """
    response = 'Failed'
    if request.method == 'POST':
        # Get the required parameters
        save_to_db_flag = request.POST['save_to_db_flag']
        peer_set = ast.literal_eval(request.POST['peer_set'])
        deal_id = request.POST['deal_id']
        deal_object = MA_Deals.objects.get(id=deal_id)
        peer_set.append(deal_object.target_ticker + " Equity")
        # Save to Database if checkbox value is ON
        # Get the Required charts for each Peer and save it in the DB
        charts = {}
        # 1. Get EV_EBITDA Charts
        start_date_yyyymmdd = (datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d')
        end_date_yyyymmdd = datetime.datetime.now().strftime('%Y%m%d')

        peer_clear_flag = False  # Flag to Track the first peer on line no 239.
        # For deleting the peers already in the system and adding the new ones..

        for eachPeer in peer_set:
            ev_ebitda_chart_ltm = get_ev_ebitda(eachPeer, start_date_yyyymmdd, end_date_yyyymmdd, 'ltm',
                                                mneumonic='CURRENT_EV_TO_T12M_EBITDA').reset_index().rename(
                                                columns={"index": "date", 0: "ev_ebitda_value"})
            ev_ebitda_chart_1bf = get_ev_ebitda(eachPeer, start_date_yyyymmdd, end_date_yyyymmdd, '1bf',
                                                mneumonic='BEST_CUR_EV_TO_EBITDA').reset_index().rename(
                                                columns={"index": "date", 0: "ev_ebitda_value"})
            ev_ebitda_chart_2bf = get_ev_ebitda(eachPeer, start_date_yyyymmdd, end_date_yyyymmdd, '2bf',
                                                mneumonic='BEST_CUR_EV_TO_EBITDA').reset_index().rename(
                                                columns={"index": "date", 0: "ev_ebitda_value"})

            pe_ratio_ltm = get_pe_ratio(eachPeer, start_date_yyyymmdd, end_date_yyyymmdd, 'ltm',
                                        mneumonic='T12M_DIL_PE_CONT_OPS').reset_index().rename(
                                        columns={"index": "date", 0: "pe_ratio"})
            pe_ratio_1bf = get_pe_ratio(eachPeer, start_date_yyyymmdd, end_date_yyyymmdd, '1bf',
                                        mneumonic='BEST_PE_RATIO').reset_index().rename(
                                        columns={"index": "date", 0: "pe_ratio"})
            pe_ratio_2bf = get_pe_ratio(eachPeer, start_date_yyyymmdd, end_date_yyyymmdd, '2bf',
                                        mneumonic='BEST_PE_RATIO').reset_index().rename(
                                        columns={"index": "date", 0: "pe_ratio"})
            fcf_yield = get_fcf_yield(eachPeer, start_date_yyyymmdd, end_date_yyyymmdd).rename(
                                        columns={"Date": "date", 'FCF yield': "p_fcf_value"})

            if save_to_db_flag == 'ON':
                # First Delete Existing Peers
                if not peer_clear_flag:
                    MA_Deals_PeerSet.objects.filter(deal_id=deal_id).delete()
                    peer_clear_flag = True
                # Add New Peers
                MA_Deals_PeerSet(deal_id=deal_id, peer=eachPeer,
                                 ev_ebitda_chart_ltm=ev_ebitda_chart_ltm.to_json(orient='records'),
                                 ev_ebitda_chart_1bf=ev_ebitda_chart_1bf.to_json(orient='records'),
                                 ev_ebitda_chart_2bf=ev_ebitda_chart_2bf.to_json(orient='records'),
                                 pe_ratio_chart_ltm=pe_ratio_ltm.to_json(orient='records'),
                                 pe_ratio_chart_1bf=pe_ratio_1bf.to_json(orient='records'),
                                 pe_ratio_chart_2bf=pe_ratio_2bf.to_json(orient='records'),
                                 fcf_yield_chart=fcf_yield.to_json(orient='records')).save()

            charts[eachPeer] = {'ev_ebitda_ltm': ev_ebitda_chart_ltm.to_json(orient='records'),
                                'ev_ebitda_1bf': ev_ebitda_chart_1bf.to_json(orient='records'),
                                'ev_ebitda_2bf': ev_ebitda_chart_2bf.to_json(orient='records'),
                                'pe_ratio_ltm': pe_ratio_ltm.to_json(orient='records'),
                                'pe_ratio_1bf': pe_ratio_1bf.to_json(orient='records'),
                                'pe_ratio_2bf': pe_ratio_2bf.to_json(orient='records'),
                                'fcf_yield': fcf_yield.to_json(orient='records')}

        response = json.dumps(charts)

    return HttpResponse(response)


def add_new_mna_idea(request):
    """
    :param request: Request Object containing fields for adding a new Merger Arb IDEA Deal
    :return: Failure/Success string to the front-end
    """
    response = 'Failed'
    if request.method == 'POST':
        # Retrieve the Parameters
        deal_name = request.POST['deal_name']
        analyst = request.POST['analyst']
        target_ticker = request.POST['target_ticker']
        acquirer_ticker = request.POST['acquirer_ticker']
        deal_cash_terms = request.POST['deal_cash_terms']
        deal_share_terms = request.POST['deal_stock_terms']
        deal_value = request.POST['deal_value']
        status = 'Simulating'  # Set simulation status
        created = datetime.datetime.now().date()

        # Save to New Deal Model
        deal_object = MA_Deals(deal_name=deal_name, analyst=analyst, target_ticker=target_ticker,
                               acquirer_ticker=acquirer_ticker, deal_cash_terms=deal_cash_terms,
                               deal_share_terms=deal_share_terms,
                               deal_value=deal_value, status=status, created=created)
        deal_object.save()
        response = 'Success'

    return HttpResponse(response)


def update_comments(request):
    """
    :param request: Request Object containing fields for updating Merger Arb Comment
    :return: Failure/Success string to the front-end
    """
    response = 'Failed'
    if request.method == 'POST':
        # Get the Parameters
        try:
            deal_id_under_consideration = request.POST['deal_id']
            comments = request.POST['comments']
            MA_Deals_Notes.objects.update_or_create(deal_id=deal_id_under_consideration,
                                                    defaults={'note': comments, 'last_edited': datetime.datetime.now()})
            MA_Deals.objects.update_or_create(id=deal_id_under_consideration,
                                              defaults={'last_modified': datetime.datetime.now()})
            response = 'Success'
        except Exception as exception:
            print(exception)
            response = 'Failed'

    return HttpResponse(response)


def mna_idea_run_scenario_analysis(request):
    """
    :param request: Request Object containing fields for performing Deal Scenario Analysis
    :return: JSON encoded analysis result
    """
    if request.method == 'POST':
        try:
            # Get all the required parameters
            cash_terms = float(request.POST['cash_terms'])
            share_terms = float(request.POST['share_terms'])
            aum = float(request.POST['aum'])
            deal_upside = float(request.POST['deal_upside'])
            deal_downside = float(request.POST['deal_downside'])
            target_current_price = float(request.POST['target_current_price'])
            target_shares_outstanding = float(request.POST['target_shares_outstanding'])
            target_shares_float = float(request.POST['target_shares_float'])
            acquirer_upside = float(request.POST['acquirer_upside'] if 'acquirer_upside' in request.POST else 0)
            target_last_price = float(request.POST['target_last_price'])
            deal_id = request.POST['deal_id']
            stock_component_involved = False

            if share_terms > 0:
                stock_component_involved = True  # Check if stock component is involved
                break_spread = ((acquirer_upside * share_terms) + cash_terms) - deal_downside
                spread = deal_upside - target_last_price

            # Create Deal Break Scenario First
            bps_to_lose = [0.15, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.75, 0.80, 0.90, 1.0]

            break_df = pd.DataFrame(bps_to_lose, columns=['bps_impact'])
            deal_break_change = (deal_downside - target_current_price) if not stock_component_involved else (
                                 spread - break_spread)

            # Change Upside/downside based on Stock component
            if stock_component_involved:
                deal_upside = spread
                deal_downside = spread - break_spread

            break_df['shares'] = ((aum * break_df['bps_impact'] * 0.01) / abs(deal_break_change)).astype(int)
            break_df['NAV break'] = round(100.0 * ((break_df['shares'] * deal_break_change) / aum), 2)
            break_df['% nav'] = round(100.0 * ((break_df['shares'] * target_last_price) / aum), 2)
            break_df['% of S/O'] = round(100.0 * (break_df['shares'] / target_shares_outstanding), 2)
            break_df['% of Float'] = round(100.0 * (break_df['shares'] / target_shares_float), 2)

            # Repeat the above for 75-25 Probability Scenario
            deal_scenario_75_25 = pd.DataFrame(bps_to_lose, columns=['bps_impact'])
            new_downside = -(abs((0.75 * deal_upside) + (0.25 * abs(deal_downside))))
            deal_break_change_scenario = new_downside - deal_upside if not stock_component_involved else new_downside
            deal_scenario_75_25['shares'] = (
                    (aum * deal_scenario_75_25['bps_impact'] * 0.01) / abs(deal_break_change_scenario)).astype(int)
            deal_scenario_75_25['NAV 75/25'] = round(
                100.0 * ((deal_scenario_75_25['shares'] * deal_break_change_scenario) / aum), 2)
            deal_scenario_75_25['NAV break'] = round(
                100.0 * ((deal_scenario_75_25['shares'] * deal_break_change) / aum), 2)
            deal_scenario_75_25['% nav'] = round(100.0 * ((deal_scenario_75_25['shares'] * target_last_price) / aum), 2)
            deal_scenario_75_25['% of S/O'] = round(100.0 * (deal_scenario_75_25['shares'] / target_shares_outstanding),
                                                    2)
            deal_scenario_75_25['% of Float'] = round(100.0 * (deal_scenario_75_25['shares'] / target_shares_float), 2)

            # Repeat for 55/45 Probability
            # Repeat the above for 75-25 Probability Scenario
            deal_scenario_55_45 = pd.DataFrame(bps_to_lose, columns=['bps_impact'])
            new_downside = -(abs((0.55 * deal_upside) + (0.45 * abs(deal_downside))))
            change_55_45 = new_downside - deal_upside if not stock_component_involved else new_downside
            deal_scenario_55_45['shares'] = (
                    (aum * deal_scenario_55_45['bps_impact'] * 0.01) / abs(change_55_45)).astype(int)
            deal_scenario_55_45['NAV 55/45'] = round(100.0 * ((deal_scenario_55_45['shares'] * change_55_45) / aum), 2)
            deal_scenario_55_45['NAV break'] = round(
                100.0 * ((deal_scenario_55_45['shares'] * deal_break_change) / aum), 2)
            deal_scenario_55_45['% nav'] = round(100.0 * ((deal_scenario_55_45['shares'] * target_last_price) / aum), 2)
            deal_scenario_55_45['% of S/O'] = round(100.0 * (deal_scenario_55_45['shares'] / target_shares_outstanding),
                                                    2)
            deal_scenario_55_45['% of Float'] = round(100.0 * (deal_scenario_55_45['shares'] / target_shares_float), 2)

            # Save both these Deal Dfs into the Database for future Retrieval
            scenario_change = deal_break_change_scenario
            break_change = deal_break_change
            scenario_change_55_45 = change_55_45

            break_scenario = break_df.to_json(orient='records')
            scenario_75_25 = deal_scenario_75_25.to_json(orient='records')
            scenario_change = float(round(scenario_change, 2))
            break_change = float(round(break_change, 2))
            scenario_change_55_45 = float(round(scenario_change_55_45, 2))
            scenario_55_45 = deal_scenario_55_45.to_json(orient='records')

            scenario_dfs = json.dumps({'break_scenario': break_scenario, 'scenario_75_25': scenario_75_25,
                                       'scenario_change': scenario_change, 'break_change': break_change,
                                       'scenario_change_55_45': scenario_change_55_45,
                                       'scenario_55_45': scenario_55_45})

            # Save to DB
            MA_Deals_Scenario_Analysis.objects.update_or_create(deal_id=deal_id,
                                                                defaults={'break_scenario_df': break_scenario,
                                                                          'scenario_75_25': scenario_75_25,
                                                                          'scenario_change': scenario_change,
                                                                          'break_change': break_change,
                                                                          'scenario_change_55_45': scenario_change_55_45,
                                                                          'scenario_55_45': scenario_55_45})

            return HttpResponse(scenario_dfs)
        except Exception as exception:
            print(exception)
            return HttpResponse('Failed')


def mna_idea_database(request):
    """
    :param request: Request Object with no fields
    :return: All Deals in the Merger Arb IDEA Database
    """
    deals_df = MA_Deals.objects.all()
    return render(request, 'mna_idea_database.html', {'deals_df': deals_df})


def show_mna_idea(request):
    """
        :param request: Request Object containing ID for the deal to populate
        :return: JSON encoded response object to display the deal
    """
    deal_id = request.GET['mna_idea_id']
    # 1. Get all Core parameters for this deal
    deal_core = MA_Deals.objects.get(id=deal_id)
    # 2. Get Weekly Downside Estimates for the deal id

    # 3. Get related News/Notes for this Idea
    # deal_notes = serializers.serialize('json',MA_Deals_Notes.objects.filter(deal_id=deal_id))
    historical_downside_estimates = MA_Deals_WeeklyDownsideEstimates.objects.filter(deal_id=deal_id)
    deal_note = MA_Deals_Notes.objects.filter(deal_id=deal_id).first()

    # 4. Get The Lawyer Reports
    deal_lawyer_reports = MA_Deals_Lawyer_Reports.objects.filter(deal_id=deal_id)

    # # 5. Get the Weekly downside Estimates for the Current Week....
    # #Get Week no, start and End dates
    # now = datetime.datetime.now()
    # # Get the Current Week number from the timestamp and the start and end of the week for historical retrieval
    # year, week_number = now.date().isocalendar()[0:2]
    # Isocalendar returns a tuple with Year, Week number and weekday in respective order...
    # start_day, end_day = get_start_end_dates(year, week_number)
    # current week starts on Monday and ends the following Sunday...

    weekly_downside_estimates = MA_Deals_WeeklyDownsideEstimates.objects.filter(deal=deal_id)
    overlay_weekly_downside_estimate = None
    if not weekly_downside_estimates:
        weekly_downside_estimates = {}
    else:
        overlay_weekly_downside_estimate = weekly_downside_estimates.first()

    target_ticker = deal_core.target_ticker if "EQUITY" in deal_core.target_ticker else \
        deal_core.target_ticker + " EQUITY"

    created_date = deal_core.created.strftime('%Y%m%d')
    # Get PX_LAST, EQ_SH_OUT, EQY_FLOAT * 1000000

    if api_host is None:
        return HttpResponse('No Bloomberg Hosts available!')

    r_refdata = requests.get("http://" + api_host + "/wic/api/v1.0/general_refdata",
                             params={'idtype': "tickers", "fields": "PX_LAST,EQY_SH_OUT,EQY_FLOAT",
                                     "tickers": ','.join([target_ticker]),
                                     "override": "",
                                     "start_date": created_date,
                                     "end_date": datetime.datetime.now().strftime('%Y%m%d')},
                             timeout=15)  # Set a 15 secs Timeout

    # Make a historical Data Request for Target and Acquirer Tickers
    acquirer_ticker = deal_core.acquirer_ticker if "EQUITY" in deal_core.acquirer_ticker \
        else deal_core.acquirer_ticker + " EQUITY"

    main_tickers = [target_ticker]

    if acquirer_ticker is not None:
        main_tickers.append(acquirer_ticker)

    r_histdata = requests.get("http://" + api_host + "/wic/api/v1.0/general_histdata",
                              params={'idtype': "tickers", "fields": "PX_LAST",
                                      "tickers": ','.join(main_tickers),
                                      "override": "",
                                      "start_date": (datetime.datetime.now() - relativedelta(months=12)).strftime(
                                          '%Y%m%d'),
                                      "end_date": datetime.datetime.now().strftime('%Y%m%d')},
                              timeout=15)  # Set a 15 secs Timeout

    ref_data_results = r_refdata.json()['results']

    eqy_float = 0
    eqy_sh_out = 0
    target_last_px = 0

    try:
        eqy_float = int(round(float(ref_data_results[0][target_ticker]['fields']['EQY_FLOAT'][0]) * 1000000))
        eqy_sh_out = int(round(float(ref_data_results[0][target_ticker]['fields']['EQY_SH_OUT'][0]) * 1000000))
        target_last_px = float(ref_data_results[0][target_ticker]['fields']['PX_LAST'][0])
    except KeyError as KE:
        print(KE)

    # Process the Historical Data Request
    hist_data_results = r_histdata.json()['results']
    px_last_historical = json.dumps(hist_data_results[0][target_ticker])

    # Get the Previous Analysis (if any)
    scenario_analysis_object = MA_Deals_Scenario_Analysis.objects.filter(deal_id=deal_id).first()

    deal_note = '' if not deal_note else deal_note
    scenario_analysis_object = '' if not scenario_analysis_object else scenario_analysis_object

    try:
        px_last_historical_acquirer = json.dumps(hist_data_results[1][acquirer_ticker])
    except Exception as exception:
        print(exception)    # Log this Exception
        px_last_historical_acquirer = None
    try:
        cix_histdata = requests.get("http://" + api_host + "/wic/api/v1.0/general_histdata",
                                    params={'idtype': "tickers", "fields": "PX_LAST",
                                            "tickers": ','.join([deal_core.cix_index]),
                                            "override": "",
                                            "start_date": (datetime.datetime.now() - relativedelta(months=12)).strftime(
                                                '%Y%m%d'),
                                            "end_date": datetime.datetime.now().strftime('%Y%m%d')},
                                    timeout=15)  # Set a 15 secs Timeout
        hist_data_results = cix_histdata.json()['results']
        px_last_cix_index = json.dumps(hist_data_results[0][deal_core.cix_index]['fields'])
    except Exception as exception:
        print(exception)
        px_last_cix_index = None

    try:
        spread_histdata = requests.get("http://" + api_host + "/wic/api/v1.0/general_histdata",
                                       params={'idtype': "tickers", "fields": "PX_LAST",
                                               "tickers": ','.join([deal_core.spread_index]),
                                               "override": "",
                                               "start_date": (
                                                           datetime.datetime.now() - relativedelta(months=12)).strftime(
                                                   '%Y%m%d'),
                                               "end_date": datetime.datetime.now().strftime('%Y%m%d')},
                                       timeout=15)  # Set a 15 secs Timeout
        hist_data_results = spread_histdata.json()['results']
        px_last_spread_index = json.dumps(hist_data_results[0][deal_core.spread_index]['fields'])
    except Exception as exception:
        print(exception)
        px_last_spread_index = None

    peer_charts = {}
    # Get Peer-set if present
    related_peers = MA_Deals_PeerSet.objects.filter(deal_id=deal_id)
    for eachPeer in related_peers:
        peer_charts[eachPeer.peer] = {'ev_ebitda_ltm': eachPeer.ev_ebitda_chart_ltm,
                                      'ev_ebitda_1bf': eachPeer.ev_ebitda_chart_1bf,
                                      'ev_ebitda_2bf': eachPeer.ev_ebitda_chart_2bf,
                                      'pe_ratio_ltm': eachPeer.pe_ratio_chart_ltm,
                                      'pe_ratio_1bf': eachPeer.pe_ratio_chart_1bf,
                                      'pe_ratio_2bf': eachPeer.pe_ratio_chart_2bf,
                                      'fcf_yield': eachPeer.fcf_yield_chart}

    return render(request, 'show_mna_idea.html',
                  {'deal_core': deal_core,
                   'deal_note': deal_note, 'fund_aum': deal_core.fund_aum,
                   'eqy_float': eqy_float, 'eqy_sh_out': eqy_sh_out, 'target_px_last': target_last_px,
                   'px_last_historical': px_last_historical, 'px_last_historical_acquirer': px_last_historical_acquirer,
                   'target_ticker': target_ticker, 'acquirer_ticker': acquirer_ticker,
                   'scenario_analysis_object': scenario_analysis_object, 'peer_charts': json.dumps(peer_charts),
                   'deal_lawyer_reports': deal_lawyer_reports, 'weekly_downside_estimates': weekly_downside_estimates,
                   'historical_downside_estimates': historical_downside_estimates,
                   'overlay_weekly_downside_estimate': overlay_weekly_downside_estimate,
                   'px_last_cix_index': px_last_cix_index, 'px_last_spread_index': px_last_spread_index
                   })

# endregion


# region ESS IDEA Database

def show_ess_idea(request):
    """
        :param request: Request Object containing ID for the ESS IDEA to be displayed
        :return: JSON encoded Object with IDEA Sections to be displayed on the front-end
    """
    #try:

    if 'version' in request.GET.keys():
        # Use POST for a different Version Request...
        version_requested = request.GET['version']
        deal_id = request.GET['ess_idea_id']
        # First get the deal key and then get the request version
        deal_key = ESS_Idea.objects.get(id=deal_id).deal_key
        # Use this deal key and version no. combination to find the right deal_object
        ess_idea = ESS_Idea.objects.get(deal_key=deal_key, version_number=version_requested)
        latest_version = ess_idea.version_number
        version_numbers = ESS_Idea.objects.filter(deal_key=deal_key).values_list('version_number', flat=True)
    else:

        deal_id = request.GET['ess_idea_id']

        latest_version = ESS_Idea.objects.filter(id=deal_id).latest(
            'version_number'
        ).version_number

        # First Retrieve DealKey
        deal_key = ESS_Idea.objects.get(id=deal_id).deal_key
        version_numbers = ESS_Idea.objects.filter(deal_key=deal_key).values_list('version_number', flat=True)
        ess_idea = ESS_Idea.objects.get(id=deal_id, version_number=latest_version)

    news_master = NewsMaster.objects.filter(tickers__contains=ess_idea.alpha_ticker.split(' ')[0])
    notes_master = NotesMaster.objects.filter(tickers__contains=ess_idea.alpha_ticker.split(' ')[0])
    alpha_chart = ess_idea.alpha_chart.replace("\'", "\"")
    hedge_chart = ess_idea.hedge_chart.replace("\'", "\"")
    event_premium_chart = ess_idea.event_premium_chart.replace("\'", "\"")
    implied_probability_chart = ess_idea.implied_probability_chart.replace("\'", "\"")
    market_neutral_chart = ess_idea.market_neutral_chart.replace("\'", "\"")
    related_peers = ESS_Peers.objects.select_related().filter(ess_idea_id_id=ess_idea.id, version_number=latest_version)

    # Get Upside/Downside Record Changes
    upside_downside_records = ESS_Idea_Upside_Downside_Change_Records.objects.filter(deal_key=ess_idea.deal_key).values('date_updated', 'pt_up', 'pt_wic', 'pt_down')

    upside_downside_records_df = read_frame(upside_downside_records)
    upside_downside_records_df['date_updated'] = upside_downside_records_df['date_updated'].apply(str)

    ev_ebitda_chart_ltm = []
    ev_ebitda_chart_1bf = []
    ev_ebitda_chart_2bf = []

    ev_sales_chart_ltm = []
    ev_sales_chart_1bf = []
    ev_sales_chart_2bf = []

    p_eps_chart_ltm = []
    p_eps_chart_1bf = []
    p_eps_chart_2bf = []

    p_fcf_chart = []

    ev_ebitda_chart_ltm.append(ess_idea.ev_ebitda_chart_ltm)
    ev_ebitda_chart_1bf.append(ess_idea.ev_ebitda_chart_1bf)
    ev_ebitda_chart_2bf.append(ess_idea.ev_ebitda_chart_2bf)

    ev_sales_chart_ltm.append(ess_idea.ev_sales_chart_ltm)
    ev_sales_chart_1bf.append(ess_idea.ev_sales_chart_1bf)
    ev_sales_chart_2bf.append(ess_idea.ev_sales_chart_2bf)

    p_eps_chart_ltm.append(ess_idea.p_eps_chart_ltm)
    p_eps_chart_1bf.append(ess_idea.p_eps_chart_1bf)
    p_eps_chart_2bf.append(ess_idea.p_eps_chart_2bf)

    p_fcf_chart.append(ess_idea.fcf_yield_chart)

    peer_tickers = []
    peer_tickers.append(ess_idea.alpha_ticker)
    for peer_object in related_peers:
        peer_tickers.append(peer_object.ticker)

        ev_ebitda_chart_ltm.append(peer_object.ev_ebitda_chart_ltm)
        ev_ebitda_chart_1bf.append(peer_object.ev_ebitda_chart_1bf)
        ev_ebitda_chart_2bf.append(peer_object.ev_ebitda_chart_2bf)

        ev_sales_chart_ltm.append(peer_object.ev_sales_chart_ltm)
        ev_sales_chart_1bf.append(peer_object.ev_sales_chart_1bf)
        ev_sales_chart_2bf.append(peer_object.ev_sales_chart_2bf)

        p_eps_chart_ltm.append(peer_object.p_eps_chart_ltm)
        p_eps_chart_1bf.append(peer_object.p_eps_chart_1bf)
        p_eps_chart_2bf.append(peer_object.p_eps_chart_2bf)

        p_fcf_chart.append(peer_object.p_fcf_chart)

    summary_dictionary = {}

    ev_ebitda_bf1_values = np.array(
        list(map(lambda x: float(x) if x != 'N/A' else 0, related_peers.all().values_list('ev_ebitda_bf1',
                                                                                          flat=True))))

    ev_ebitda_bf1_values = [] if len(ev_ebitda_bf1_values) == 0 else np.round(
        ev_ebitda_bf1_values[ev_ebitda_bf1_values != 0], decimals=2)

    #  Get Peers EV/Sales values...
    ev_sales_bf1_values = np.array(
        list(map(lambda x: float(x) if x != 'N/A' else 0, related_peers.all().values_list('ev_sales_bf1',
                                                                                          flat=True))))

    ev_sales_bf1_values = [] if len(ev_sales_bf1_values) == 0 else np.round(
        ev_sales_bf1_values[ev_sales_bf1_values != 0], decimals=2)

    summary_dictionary['ev_ebitda_bf1_max'] = 0 if len(ev_ebitda_bf1_values) == 0 else max(ev_ebitda_bf1_values)
    summary_dictionary['ev_ebitda_bf1_mean'] = 0 if len(ev_ebitda_bf1_values) == 0 else np.round(
        np.mean(ev_ebitda_bf1_values), decimals=2)
    summary_dictionary['ev_ebitda_bf1_min'] = 0 if len(ev_ebitda_bf1_values) == 0 else min(ev_ebitda_bf1_values)

    summary_dictionary['ev_sales_bf1_max'] = 0 if len(ev_sales_bf1_values) == 0 else max(ev_sales_bf1_values)
    summary_dictionary['ev_sales_bf1_mean'] = 0 if len(ev_sales_bf1_values) == 0 else np.round(
        np.mean(ev_sales_bf1_values), decimals=2)
    summary_dictionary['ev_sales_bf1_min'] = 0 if len(ev_sales_bf1_values) == 0 else min(ev_sales_bf1_values)

    ev_ebitda_bf2 = np.array(
        list(map(lambda x: float(x) if x != 'N/A' else 0, related_peers.all().values_list('ev_ebitda_bf2', flat=True))))
    ev_ebitda_bf2 = [] if len(ev_ebitda_bf2) == 0 else np.round(ev_ebitda_bf2[ev_ebitda_bf2 != 0], decimals=2)

    # Get Ev/Sales
    ev_sales_bf2 = np.array(
        list(map(lambda x: float(x) if x != 'N/A' else 0, related_peers.all().values_list('ev_sales_bf2', flat=True))))

    ev_sales_bf2 = [] if len(ev_sales_bf2) == 0 else np.round(ev_sales_bf2[ev_sales_bf2 != 0], decimals=2)

    summary_dictionary['ev_ebitda_bf2_max'] = 0 if len(ev_ebitda_bf2) == 0 else max(ev_ebitda_bf2)
    summary_dictionary['ev_ebitda_bf2_mean'] = 0 if len(ev_ebitda_bf2) == 0 else np.round(np.mean(ev_ebitda_bf2),
                                                                                          decimals=2)
    summary_dictionary['ev_ebitda_bf2_min'] = 0 if len(ev_ebitda_bf2) == 0 else min(ev_ebitda_bf2)

    summary_dictionary['ev_sales_bf2_max'] = 0 if len(ev_sales_bf2) == 0 else max(ev_sales_bf2)
    summary_dictionary['ev_sales_bf2_mean'] = 0 if len(ev_sales_bf2) == 0 else np.round(np.mean(ev_sales_bf2),
                                                                                        decimals=2)
    summary_dictionary['ev_sales_bf2_min'] = 0 if len(ev_sales_bf2) == 0 else min(ev_sales_bf2)

    p_e_bf1 = np.array(
        list(map(lambda x: float(x) if x != 'N/A' else 0, related_peers.all().values_list('p_e_bf1', flat=True))))
    p_e_bf1 = [] if len(p_e_bf1) == 0 else np.round(p_e_bf1[p_e_bf1 != 0], decimals=2)

    summary_dictionary['p_e_bf1_max'] = 0 if len(p_e_bf1) == 0 else max(p_e_bf1)
    summary_dictionary['p_e_bf1_mean'] = 0 if len(p_e_bf1) == 0 else np.round(np.mean(p_e_bf1), decimals=2)
    summary_dictionary['p_e_bf1_min'] = 0 if len(p_e_bf1) == 0 else min(p_e_bf1)

    p_e_bf2 = np.array(
        list(map(lambda x: float(x) if x != 'N/A' else 0, related_peers.all().values_list('p_e_bf2', flat=True))))
    p_e_bf2 = [] if len(p_e_bf2) == 0 else np.round(p_e_bf2[p_e_bf2 != 0], decimals=2)

    summary_dictionary['p_e_bf2_max'] = 0 if len(p_e_bf2) == 0 else max(p_e_bf2)
    summary_dictionary['p_e_bf2_mean'] = 0 if len(p_e_bf2) == 0 else np.round(np.mean(p_e_bf2), decimals=2)
    summary_dictionary['p_e_bf2_min'] = 0 if len(p_e_bf2) == 0 else min(p_e_bf2)

    fcf_yield_bf1 = np.array(
        list(map(lambda x: float(x) if x != 'N/A' else 0, related_peers.all().values_list('fcf_yield_bf1',
                                                                                          flat=True))))
    fcf_yield_bf1 = [] if len(fcf_yield_bf1) == 0 else np.round(fcf_yield_bf1[fcf_yield_bf1 != 0], decimals=2)

    summary_dictionary['fcf_yield_bf1_max'] = 0 if len(fcf_yield_bf1) == 0 else max(fcf_yield_bf1)
    summary_dictionary['fcf_yield_bf1_mean'] = 0 if len(fcf_yield_bf1) == 0 else np.round(np.mean(fcf_yield_bf1),
                                                                                          decimals=2)
    summary_dictionary['fcf_yield_bf1_min'] = 0 if len(fcf_yield_bf1) == 0 else min(fcf_yield_bf1)

    fcf_yield_bf2 = np.array(
        list(map(lambda x: float(x) if x != 'N/A' else 0, related_peers.all().values_list('fcf_yield_bf2',
                                                                                          flat=True))))
    fcf_yield_bf2 = [] if len(fcf_yield_bf2) == 0 else np.round(fcf_yield_bf2[fcf_yield_bf2 != 0], decimals=2)

    summary_dictionary['fcf_yield_bf2_max'] = 0 if len(fcf_yield_bf2) == 0 else max(fcf_yield_bf2)
    summary_dictionary['fcf_yield_bf2_mean'] = 0 if len(fcf_yield_bf2) == 0 else np.round(np.mean(fcf_yield_bf2),
                                                                                          decimals=2)
    summary_dictionary['fcf_yield_bf2_min'] = 0 if len(fcf_yield_bf2) == 0 else min(fcf_yield_bf2)

    # Append the Alpha Valuation Metrics

    p_fcf_chart.append(ess_idea.fcf_yield_chart)

    if ess_idea.bull_thesis_model == 'NA':
        bull_thesis_model = None
    else:
        bull_thesis_model = ess_idea.bull_thesis_model

    if ess_idea.our_thesis_model == 'NA':
        our_thesis_model = None
    else:
        our_thesis_model = ess_idea.our_thesis_model

    if ess_idea.bear_thesis_model == 'NA':
        bear_thesis_model = None
    else:
        bear_thesis_model = ess_idea.bear_thesis_model

    ev_ebitda_chart_1bf_df = pd.DataFrame()
    ev_ebitda_chart_ltm_df = pd.DataFrame()
    ev_ebitda_chart_2bf_df = pd.DataFrame()

    ev_sales_chart_1bf_df = pd.DataFrame()
    ev_sales_chart_ltm_df = pd.DataFrame()
    ev_sales_chart_2bf_df = pd.DataFrame()

    # ---- Get MOSAIC Sum ---------
    mosaic_sum = ess_idea.m_value + ess_idea.o_value + ess_idea.s_value + ess_idea.a_value + ess_idea.i_value + \
                 ess_idea.c_value

    for i in range(len(p_fcf_chart)):
        if i == 0:
            # assign first dataframe
            p_fcf_chart_df = pd.DataFrame.from_dict(json.loads(p_fcf_chart[i]))
            continue
        # Merge each dataframe into each other and finally append the merged Results to account for missing data
        p_fcf_chart_ = pd.DataFrame.from_dict(json.loads(p_fcf_chart[i]))
        # Merge with Next DataFrame on Date
        p_fcf_chart_df = pd.merge(p_fcf_chart_df, p_fcf_chart_, on='date', how='outer')

    for i in range(len(ev_ebitda_chart_ltm)):
        if i == 0:
            # assign first dataframe
            ev_ebitda_chart_ltm_df = pd.DataFrame.from_dict(json.loads(ev_ebitda_chart_ltm[i]))
            continue
        # Merge each dataframe into each other and finally append the merged Results to account for missing data
        ev_ebitda_chart_ltm_ = pd.DataFrame.from_dict(json.loads(ev_ebitda_chart_ltm[i]))
        # Merge with Next DataFrame on Date
        ev_ebitda_chart_ltm_df = pd.merge(ev_ebitda_chart_ltm_df, ev_ebitda_chart_ltm_, on='date', how='outer')

    # ----- Repeat for 1BF ------------

    for i in range(len(ev_ebitda_chart_1bf)):
        if i == 0:
            # assign first dataframe
            ev_ebitda_chart_1bf_df = pd.DataFrame.from_dict(json.loads(ev_ebitda_chart_1bf[i]))
            continue
        # Merge each dataframe into each other and finally append the merged Results to account for missing data
        ev_ebitda_chart_1bf_ = pd.DataFrame.from_dict(json.loads(ev_ebitda_chart_1bf[i]))
        # Merge with Next DataFrame on Date
        ev_ebitda_chart_1bf_df = pd.merge(ev_ebitda_chart_1bf_df, ev_ebitda_chart_1bf_, on='date', how='outer')

    # Repeat for 2BF
    for i in range(len(ev_ebitda_chart_2bf)):
        if i == 0:
            # assign first dataframe
            ev_ebitda_chart_2bf_df = pd.DataFrame.from_dict(json.loads(ev_ebitda_chart_2bf[i]))
            continue
        # Merge each dataframe into each other and finally append the merged Results to account for missing data
        ev_ebitda_chart_2bf_ = pd.DataFrame.from_dict(json.loads(ev_ebitda_chart_2bf[i]))
        # Merge with Next DataFrame on Date
        ev_ebitda_chart_2bf_df = pd.merge(ev_ebitda_chart_2bf_df, ev_ebitda_chart_2bf_, on='date', how='outer')

    # Merge with Alpha Ticker

    ev_ebitda_chart_ltm_df = pd.merge(ev_ebitda_chart_ltm_df,
                                      pd.DataFrame.from_dict(json.loads(ess_idea.ev_ebitda_chart_ltm)), on='date',
                                      how='outer') if len(ev_ebitda_chart_ltm) > 0 else pd.DataFrame()
    ev_ebitda_chart_1bf_df = pd.merge(ev_ebitda_chart_1bf_df,
                                      pd.DataFrame.from_dict(json.loads(ess_idea.ev_ebitda_chart_1bf)), on='date',
                                      how='outer') if len(ev_ebitda_chart_1bf_df) > 0 else pd.DataFrame()
    ev_ebitda_chart_2bf_df = pd.merge(ev_ebitda_chart_2bf_df,
                                      pd.DataFrame.from_dict(json.loads(ess_idea.ev_ebitda_chart_2bf)), on='date',
                                      how='outer') if len(ev_ebitda_chart_2bf_df) > 0 else pd.DataFrame()
    ev_ebitda_chart_2bf_df = ev_ebitda_chart_2bf_df.replace(r'\s+', "NaN", regex=True).sort_values(by='date') if len(
        ev_ebitda_chart_2bf_df) > 0 else ev_ebitda_chart_2bf_df

    # Repeat for EV/Sales Multiple

    for i in range(len(ev_sales_chart_ltm)):
        if i == 0:
            # assign first dataframe
            ev_sales_chart_ltm_df = pd.DataFrame.from_dict(json.loads(ev_sales_chart_ltm[i]))
            continue
        # Merge each dataframe into each other and finally append the merged Results to account for missing data
        ev_sales_chart_ltm_ = pd.DataFrame.from_dict(json.loads(ev_sales_chart_ltm[i]))
        # Merge with Next DataFrame on Date
        ev_sales_chart_ltm_df = pd.merge(ev_sales_chart_ltm_df, ev_sales_chart_ltm_, on='date', how='outer')

    # ----- Repeat for 1BF ------------

    for i in range(len(ev_sales_chart_1bf)):
        if i == 0:
            # assign first dataframe
            ev_sales_chart_1bf_df = pd.DataFrame.from_dict(json.loads(ev_sales_chart_1bf[i]))
            continue
        # Merge each dataframe into each other and finally append the merged Results to account for missing data
        ev_sales_chart_1bf_ = pd.DataFrame.from_dict(json.loads(ev_sales_chart_1bf[i]))
        # Merge with Next DataFrame on Date
        ev_sales_chart_1bf_df = pd.merge(ev_sales_chart_1bf_df, ev_sales_chart_1bf_, on='date', how='outer')

    # Repeat for 2BF
    for i in range(len(ev_sales_chart_2bf)):
        if i == 0:
            # assign first dataframe
            ev_sales_chart_2bf_df = pd.DataFrame.from_dict(json.loads(ev_sales_chart_2bf[i]))
            continue
        # Merge each dataframe into each other and finally append the merged Results to account for missing data
        ev_sales_chart_2bf_ = pd.DataFrame.from_dict(json.loads(ev_sales_chart_2bf[i]))
        # Merge with Next DataFrame on Date
        ev_sales_chart_2bf_df = pd.merge(ev_sales_chart_2bf_df, ev_sales_chart_2bf_, on='date', how='outer')

    # Merge with Alpha Ticker

    ev_sales_chart_ltm_df = pd.merge(ev_sales_chart_ltm_df,
                                     pd.DataFrame.from_dict(json.loads(ess_idea.ev_sales_chart_ltm)), on='date',
                                     how='outer') if len(ev_sales_chart_ltm) > 0 else pd.DataFrame()
    ev_sales_chart_1bf_df = pd.merge(ev_sales_chart_1bf_df,
                                     pd.DataFrame.from_dict(json.loads(ess_idea.ev_sales_chart_1bf)), on='date',
                                     how='outer') if len(ev_sales_chart_1bf_df) > 0 else pd.DataFrame()
    ev_sales_chart_2bf_df = pd.merge(ev_sales_chart_2bf_df,
                                     pd.DataFrame.from_dict(json.loads(ess_idea.ev_sales_chart_2bf)), on='date',
                                     how='outer') if len(ev_sales_chart_2bf_df) > 0 else pd.DataFrame()
    ev_sales_chart_2bf_df = ev_sales_chart_2bf_df.replace(r'\s+', "NaN", regex=True).sort_values(by='date') if len(
        ev_sales_chart_2bf_df) > 0 else ev_sales_chart_2bf_df

    # ------------------- SIMILAR FOR PE RATIO CHARTs

    p_eps_chart_ltm_df = pd.DataFrame()
    p_eps_chart_1bf_df = pd.DataFrame()
    p_eps_chart_2bf_df = pd.DataFrame()

    for i in range(len(p_eps_chart_ltm)):
        if i == 0:
            # assign first dataframe
            p_eps_chart_ltm_df = pd.DataFrame.from_dict(json.loads(p_eps_chart_ltm[i]))
            continue
        # Merge each dataframe into each other and finally append the merged Results to account for missing data
        p_eps_chart_ltm_ = pd.DataFrame.from_dict(json.loads(p_eps_chart_ltm[i]))
        # Merge with Next DataFrame on Date
        p_eps_chart_ltm_df = pd.merge(p_eps_chart_ltm_df, p_eps_chart_ltm_, on='date', how='outer')

    # ----- Repeat for 1BF ------------
    for i in range(len(p_eps_chart_1bf)):
        if i == 0:
            # assign first dataframe
            p_eps_chart_1bf_df = pd.DataFrame.from_dict(json.loads(p_eps_chart_1bf[i]))
            continue
        # Merge each dataframe into each other and finally append the merged Results to account for missing data
        p_eps_chart_1bf_ = pd.DataFrame.from_dict(json.loads(p_eps_chart_1bf[i]))
        # Merge with Next DataFrame on Date
        p_eps_chart_1bf_df = pd.merge(p_eps_chart_1bf_df, p_eps_chart_1bf_, on='date', how='outer')

    # Repeat for 2BF
    for i in range(len(p_eps_chart_2bf)):
        if i == 0:
            # assign first dataframe
            p_eps_chart_2bf_df = pd.DataFrame.from_dict(json.loads(p_eps_chart_2bf[i]))
            continue
        # Merge each dataframe into each other and finally append the merged Results to account for missing data
        p_eps_chart_2bf_ = pd.DataFrame.from_dict(json.loads(p_eps_chart_2bf[i]))
        # Merge with Next DataFrame on Date
        p_eps_chart_2bf_df = pd.merge(p_eps_chart_2bf_df, p_eps_chart_2bf_, on='date', how='outer')

    p_eps_chart_ltm_df = pd.merge(p_eps_chart_ltm_df, pd.DataFrame.from_dict(json.loads(ess_idea.p_eps_chart_ltm)),
                                  on='date', how='outer') if len(p_eps_chart_ltm_df) > 0 else pd.DataFrame()
    p_eps_chart_1bf_df = pd.merge(p_eps_chart_1bf_df, pd.DataFrame.from_dict(json.loads(ess_idea.p_eps_chart_1bf)),
                                  on='date', how='outer') if len(p_eps_chart_1bf_df) > 0 else pd.DataFrame()
    p_eps_chart_2bf_df = pd.merge(p_eps_chart_2bf_df, pd.DataFrame.from_dict(json.loads(ess_idea.p_eps_chart_2bf)),
                                  on='date', how='outer') if len(p_eps_chart_2bf_df) > 0 else pd.DataFrame()

    col_to_rename_ev_ebitda = ['date']
    col_to_rename_ev_sales = ['date']
    col_to_rename_p_eps = ['date']
    col_to_rename_p_fcf = ['date']
    for i in range(0, len(p_eps_chart_2bf) + 1):  # +1 FOR aLPHA TICKER
        col_to_rename_ev_ebitda.append('ev_ebitda_value')
        col_to_rename_p_eps.append('pe_ratio')
        col_to_rename_p_fcf.append('p_fcf_value')
        col_to_rename_ev_sales.append('ev_sales_value')
    # Rename the Columns
    p_fcf_chart_df.columns = col_to_rename_p_fcf if len(p_fcf_chart_df) > 0 else p_fcf_chart_df.columns
    ev_ebitda_chart_ltm_df.columns = col_to_rename_ev_ebitda if len(
        ev_ebitda_chart_ltm_df) > 0 else ev_ebitda_chart_ltm_df.columns
    ev_ebitda_chart_1bf_df.columns = col_to_rename_ev_ebitda if len(
        ev_ebitda_chart_1bf_df) > 0 else ev_ebitda_chart_1bf_df.columns
    ev_ebitda_chart_2bf_df.columns = col_to_rename_ev_ebitda if len(
        ev_ebitda_chart_2bf_df) > 0 else ev_ebitda_chart_2bf_df.columns

    ev_sales_chart_ltm_df.columns = col_to_rename_ev_sales if len(
        ev_sales_chart_ltm_df) > 0 else ev_sales_chart_ltm_df.columns
    ev_sales_chart_1bf_df.columns = col_to_rename_ev_sales if len(
        ev_sales_chart_1bf_df) > 0 else ev_sales_chart_1bf_df.columns
    ev_sales_chart_2bf_df.columns = col_to_rename_ev_sales if len(
        ev_sales_chart_2bf_df) > 0 else ev_sales_chart_2bf_df.columns

    p_eps_chart_ltm_df.columns = col_to_rename_p_eps if len(p_eps_chart_ltm_df) > 0 else p_eps_chart_ltm_df.columns
    p_eps_chart_1bf_df.columns = col_to_rename_p_eps if len(p_eps_chart_1bf_df) > 0 else p_eps_chart_1bf_df.columns
    p_eps_chart_2bf_df.columns = col_to_rename_p_eps if len(p_eps_chart_2bf_df) > 0 else p_eps_chart_2bf_df.columns

    ev_ebitda_chart_ltm = []
    ev_ebitda_chart_1bf = []
    ev_ebitda_chart_2bf = []

    ev_sales_chart_ltm = []
    ev_sales_chart_1bf = []
    ev_sales_chart_2bf = []

    p_eps_chart_ltm = []
    p_eps_chart_1bf = []
    p_eps_chart_2bf = []
    p_fcf_chart = []

    # Free Cash Flow Yield - Trim values and show in Percentages
    p_fcf_chart_df['p_fcf_value'] = p_fcf_chart_df['p_fcf_value'].apply(lambda x: round(x * 100, 2))

    for i in range(1, len(ev_ebitda_chart_ltm_df.columns.values)):
        ev_sales_chart_ltm.append(str(ev_sales_chart_ltm_df.iloc[:, [0, i]].to_dict('records'))
                                  .replace('u\'', '\''))
        ev_sales_chart_1bf.append(str(ev_sales_chart_1bf_df.iloc[:, [0, i]].to_dict('records'))
                                  .replace('u\'', '\''))
        ev_sales_chart_2bf.append(str(ev_sales_chart_2bf_df.iloc[:, [0, i]].to_dict('records'))
                                  .replace('u\'', '\''))

        ev_ebitda_chart_ltm.append(str(ev_ebitda_chart_ltm_df.iloc[:, [0, i]].to_dict('records'))
                                   .replace('u\'', '\''))
        ev_ebitda_chart_1bf.append(str(ev_ebitda_chart_1bf_df.iloc[:, [0, i]].to_dict('records'))
                                   .replace('u\'', '\''))
        ev_ebitda_chart_2bf.append(str(ev_ebitda_chart_2bf_df.iloc[:, [0, i]].to_dict('records'))
                                   .replace('u\'', '\''))

        p_eps_chart_ltm.append(str(p_eps_chart_ltm_df.iloc[:, [0, i]].to_dict('records'))
                               .replace('u\'', '\''))
        p_eps_chart_1bf.append(str(p_eps_chart_1bf_df.iloc[:, [0, i]].to_dict('records'))
                               .replace('u\'', '\''))
        p_eps_chart_2bf.append(str(p_eps_chart_2bf_df.iloc[:, [0, i]].to_dict('records'))
                               .replace('u\'', '\''))

        p_fcf_chart.append(str(p_fcf_chart_df.iloc[:, [0, i]].to_dict('records')).replace('u\'', '\''))


    #Get The downside Changes for the deal
    downside_changes = ESS_Idea_Upside_Downside_Change_Records.objects.filter(deal_key=deal_key)
    if len(downside_changes) > 0:
        downside_changes = pd.DataFrame().from_records(list(downside_changes.
                                                            values(*['date_updated', 'pt_up', 'pt_down'])))
        downside_changes['date_updated'] = downside_changes['date_updated'].apply(pd.to_datetime)
        downside_changes['date_updated'] = downside_changes['date_updated'].apply(lambda x: str(x.date()))
        downside_changes.to_json(orient='records')
    # except Exception as exception:
    #     print(exception)
    #     return HttpResponse('Deal is Still being Calculated!')

    return render(request, 'show_ess_idea.html',
                  context={'news_master': news_master, 'ess_idea_object': ess_idea, 'alpha_chart': alpha_chart,
                           'hedge_chart': hedge_chart, 'event_premium_chart': event_premium_chart,
                           'implied_probability_chart': implied_probability_chart,
                           'market_neutral_chart': market_neutral_chart, 'notes_master': notes_master,
                           'ev_ebitda_chart_ltm': ev_ebitda_chart_ltm, 'ev_ebitda_chart_1bf': ev_ebitda_chart_1bf,
                           'ev_ebitda_chart_2bf': ev_ebitda_chart_2bf, 'ev_sales_chart_ltm': ev_sales_chart_ltm,
                           'ev_sales_chart_1bf': ev_sales_chart_1bf, 'ev_sales_chart_2bf': ev_sales_chart_2bf,
                           'p_eps_chart_ltm': p_eps_chart_ltm, 'p_eps_chart_1bf': p_eps_chart_1bf,
                           'p_eps_chart_2bf': p_eps_chart_2bf,
                           'p_fcf_chart': p_fcf_chart, 'peer_tickers': ','.join(peer_tickers),
                           'related_peers': related_peers, 'summary_object': summary_dictionary,
                           'bull_thesis_model': bull_thesis_model, 'bear_thesis_model': bear_thesis_model,
                           'our_thesis_model': our_thesis_model, 'mosaic_sum': mosaic_sum,
                           'version_numbers': version_numbers, 'downside_changes':downside_changes,
                           'upside_downside_records_df':upside_downside_records_df.to_json(orient='records')})


# @login_required
def edit_ess_deal(request):
    """
    :param request: Request Object containing the ID of the deal to be edited
    :return: Deal Parameters to Populate the Front-end Modal
    """
    response = {}
    if request.method == 'POST':
        if 'prepopulation_request' in request.POST:
            # Only send current data for pre-population of modal
            deal_id = request.POST['deal_id']
            latest_version = ESS_Idea.objects.filter(id=deal_id).latest(
                'version_number'
            ).version_number

            deal_object = ESS_Idea.objects.filter(id=deal_id, version_number=latest_version).values_list()
            related_peers = ESS_Peers.objects.select_related().filter(ess_idea_id_id=deal_id,
                                                                      version_number=latest_version).values_list()

            response['deal_object'] = list(deal_object)
            response['related_peers'] = list(related_peers)
            response['multiples_dict'] = ESS_Idea.objects.get(id=deal_id).multiples_dictionary.replace("\'", "\"")
    return JsonResponse(response)


def get_gics_sector(request):
    """
    View to Return GICS Sector for a Ticker
    :param request: Request object containing Security Ticker
    :return: GICS Sector or Failed string
    """
    response = 'Failed'
    if request.method == 'POST':
        ticker = request.POST['ticker']
        ticker = ticker+" EQUITY" if "EQUITY" not in ticker else ticker
        gics_sector = bbgclient.bbgclient.get_secid2field([ticker], 'ticker', ['GICS_SECTOR_NAME'], req_type='refdata',
                                            api_host=api_host)
        gics_sector = gics_sector[ticker]['GICS_SECTOR_NAME'][0]
        response = gics_sector

    return HttpResponse(response)


# @login_required
def ess_idea_database(request):
    """
    :param request: Request Object to View all ESS IDEA Deals
    :return: Render object with all ESS IDEA deals in a dataframe
    """
    df = ESS_Idea.objects.raw("SELECT  * "
                              "FROM  test_wic_db.risk_ess_idea AS A "
                              "INNER JOIN ("
                              "SELECT   "
                              "deal_key, max(version_number) as max_version "
                              "from  test_wic_db.risk_ess_idea "
                              "group by deal_key "
                              ") AS B ON A.deal_key = B.deal_key AND A.version_number = B.max_version")

    return render(request, 'ess_idea_database.html', context={'ess_idea_df': df})


@csrf_exempt
def get_celery_status(request):
    """
    :param request: Object containing ID of the Celery task
    :return: Status of the Celery Task
    """
    if request.method == 'POST':
        response = ''
        # Get the Celery Task ID
        task_id = request.POST['id']
        status = AsyncResult(task_id).state
        if status == 'PENDING':
            response = 'PENDING'

        if status == 'SUCCESS':
            response = 'SUCCESS'

        if status == 'FAILURE':
            response = 'FAILURE'

    return HttpResponse(response)


def ess_idea_save_balance_sheet(request):
    """
    :param request: Request Object containing ID of the deal
    :return: Failure/Success string based on outcome
    """
    response = 'Failed'
    if request.method == 'POST':
        deal_id = request.POST.get('deal_id')
        latest_version = ESS_Idea.objects.filter(id=deal_id).latest(
            'version_number'
        ).version_number

        deal_object = ESS_Idea.objects.get(id=deal_id, version_number=latest_version)
        balance_sheet = pd.DataFrame(pd.read_json(request.POST['balance_sheet'], orient='records', typ='series'))\
            .transpose()

        on_pt_balance_sheet = pd.DataFrame(pd.read_json(request.POST['on_pt_balance_sheet'], orient='records',
                                                        typ='series'))\
            .transpose()

        deal_object.idea_balance_sheet = balance_sheet.to_json(orient='records')
        deal_object.on_pt_balance_sheet = on_pt_balance_sheet.to_json(orient='records')
        deal_object.save()

        response = 'Success'

    return HttpResponse(response)


def ess_idea_view_balance_sheet(request):
    """
    Shows the Balance sheet Live from Bloomberg and the Adjustments (if any)
    :param request: Request object containing Deal ID
    :return: JSON Response containing the balance sheet
    """
    balance_sheet_adjustments = None
    balance_sheet = None
    on_pt_balance_sheet_adjustments = None

    if request.method == 'POST':
        deal_id = request.POST.get('deal_id')
        latest_version = ESS_Idea.objects.filter(id=deal_id).latest(
            'version_number'
        ).version_number

        deal_object = ESS_Idea.objects.get(id=deal_id, version_number=latest_version)

        balance_sheet_adjustments = deal_object.idea_balance_sheet
        on_pt_balance_sheet_adjustments = deal_object.on_pt_balance_sheet
        balance_sheet = ess_premium_analysis.multiple_underlying_df(deal_object.alpha_ticker,
                                                                    datetime.datetime.now().strftime('%Y%m%d'),
                                                                    api_host)
        if balance_sheet_adjustments is not None:
            # Previous Adjustments are saved for this deal. Fetch and display those in Adjustments table.
            balance_sheet_adjustments = pd.read_json(balance_sheet_adjustments)
            balance_sheet_adjustments['Date'] = balance_sheet_adjustments['Date'].apply(pd.to_datetime)
            balance_sheet_adjustments['Date'] = balance_sheet_adjustments['Date'].apply(lambda x: str(x.date()))
        else:
            balance_sheet_adjustments = pd.DataFrame()

        if on_pt_balance_sheet_adjustments is not None:
            # Previous Adjustments are saved for this deal. Fetch and display those in Adjustments table.
            on_pt_balance_sheet_adjustments = pd.read_json(on_pt_balance_sheet_adjustments)
            on_pt_balance_sheet_adjustments['Date'] = on_pt_balance_sheet_adjustments['Date'].apply(pd.to_datetime)
            on_pt_balance_sheet_adjustments['Date'] = on_pt_balance_sheet_adjustments['Date'].apply(lambda x: str(x.date()))
        else:
            on_pt_balance_sheet_adjustments = pd.DataFrame()

        balance_sheet['Date'] = balance_sheet['Date'].apply(pd.to_datetime)
        balance_sheet['Date'] = balance_sheet['Date'].apply(lambda x:str(x.date()))
        balance_sheet_adjustments = balance_sheet_adjustments.to_json(orient='records')
        on_pt_balance_sheet_adjustments = on_pt_balance_sheet_adjustments.to_json(orient='records')
        balance_sheet = balance_sheet.to_json(orient='records')

    return JsonResponse({'balance_sheet': balance_sheet, 'balance_sheet_adjustments': balance_sheet_adjustments,
                         'on_pt_balance_sheet_adjustments': on_pt_balance_sheet_adjustments})


def ess_idea_premium_analysis(request):
    """
    Run the Premium Analysis Module.
    :param request: Request Object containing ID of the deal
    :return: Real-time Upside/Downside of each deal
    """

    if request.method == 'POST':
        deal_id = request.POST.get('deal_id')
        latest_version = ESS_Idea.objects.filter(id=deal_id).latest(
            'version_number'
        ).version_number

        deal_object = ESS_Idea.objects.get(id=deal_id, version_number=latest_version)

        multiples_dictionary_list = ast.literal_eval(deal_object.multiples_dictionary)

        multiples_dictionary = {}
        for multiple in multiples_dictionary_list:
            for key, value in multiple.items():
                multiples_dictionary[key] = float(value)

        related_peers = ESS_Peers.objects.select_related().filter(ess_idea_id_id=deal_object.id,
                                                                  version_number=latest_version)
        peers_weights_dictionary = {}

        for each_peer in related_peers:
            peers_weights_dictionary[each_peer.ticker] = each_peer.hedge_weight / 100

        balance_sheet = deal_object.idea_balance_sheet
        on_pt_balance_sheet = deal_object.on_pt_balance_sheet
        adjustments_df = None
        on_pt_adjustments_df = None

        if balance_sheet is not None:
            adjustments_df = pd.read_json(balance_sheet, orient='records')

        if on_pt_balance_sheet is not None:
            on_pt_adjustments_df = pd.read_json(on_pt_balance_sheet, orient='records')

        df = ess_function.final_df(alpha_ticker=deal_object.alpha_ticker, cix_index=deal_object.cix_index,
                                   unaffectedDt=str(deal_object.unaffected_date),
                                   expected_close=str(deal_object.expected_close),
                                   tgtDate=str(deal_object.price_target_date),
                                   analyst_upside=deal_object.pt_up,
                                   analyst_downside=deal_object.pt_down,
                                   analyst_pt_wic=deal_object.pt_wic,
                                   peers2weight=peers_weights_dictionary,
                                   metric2weight=multiples_dictionary,
                                   api_host=api_host, adjustments_df_now=adjustments_df,
                                   adjustments_df_ptd=on_pt_adjustments_df, premium_as_percent=None,
                                   f_period="1BF")

        cix_down_price = np.round(df['Down Price (CIX)'], decimals=2)
        cix_up_price = np.round(df['Up Price (CIX)'], decimals=2)
        regression_up_price = np.round(df['Up Price (Regression)'], decimals=2)
        regression_down_price = np.round(df['Down Price (Regression)'], decimals=2)

    return HttpResponse(JsonResponse(
        {'cix_down_price': cix_down_price, 'cix_up_price': cix_up_price, 'regression_up_price': regression_up_price,
         'regression_down_price': regression_down_price}))


@csrf_exempt
def add_new_ess_idea_deal(request):
    """
    Adds/Updates a New/Existing ESS IDEA Deal into the Database. Returns the Newly Inserted Record
    as a JSON Object for Front-end Rendering. Handles Insertion/Deletion in Atomic Manner
    :param request: Request Object containing New deal addition form
    :return: ID/Error based on the execution outcome
    """

    if request.method == 'POST':
        # Get all the required fields
        # Get the Historical Data to Calculate Hedge Volatility
        try:
            bull_thesis_model_file = request.FILES.get('bull_thesis_model_file')
            our_thesis_model_file = request.FILES.get('our_thesis_model_file')
            bear_thesis_model_file = request.FILES.get('bear_thesis_model_file')
            update_id = request.POST.get('update_id')
            ticker = request.POST.get('ticker')
            situation_overview = request.POST.get('situation_overview')
            company_overview = request.POST.get('company_overview')
            bull_thesis = request.POST.get('bull_thesis')
            our_thesis = request.POST.get('our_thesis')
            bear_thesis = request.POST.get('bear_thesis')
            pt_up = float(request.POST.get('pt_up'))
            pt_wic = float(request.POST.get('pt_wic'))
            pt_down = float(request.POST.get('pt_down'))
            unaffected_date = request.POST.get('unaffected_date')
            expected_close = request.POST.get('expected_close')
            m_value = request.POST.get('m_value')
            o_value = request.POST.get('o_value')
            s_value = request.POST.get('s_value')
            a_value = request.POST.get('a_value')
            i_value = request.POST.get('i_value')
            c_value = request.POST.get('c_value')
            m_overview = request.POST.get('m_overview')
            o_overview = request.POST.get('o_overview')
            s_overview = request.POST.get('s_overview')
            a_overview = request.POST.get('a_overview')
            i_overview = request.POST.get('i_overview')
            c_overview = request.POST.get('c_overview')
            ticker_hedge_length = request.POST.get('peers_length')
            cix_index = request.POST.get('cix_index')
            price_target_date = request.POST.get('price_target_date')
            multiples = request.POST.get('multiples')
            category = request.POST.get('category')
            catalyst = request.POST.get('catalyst')
            deal_type = request.POST.get('deal_type')
            catalyst_tier = request.POST.get('catalyst_tier')
            hedges = request.POST.get('hedges')
            gics_sector = request.POST.get('gics_sector')
            lead_analyst = request.POST.get('lead_analyst')
            status = request.POST.get('ess_idea_status')
            pt_up_check = request.POST.get('pt_up_check')
            pt_down_check = request.POST.get('pt_down_check')
            pt_wic_check = request.POST.get('pt_wic_check')
            adjust_based_off = request.POST.get('adjust_based_off')
            premium_format = request.POST.get('premium_format')

            task = add_new_idea.delay(bull_thesis_model_file, our_thesis_model_file, bear_thesis_model_file, update_id,
                                      ticker, situation_overview, company_overview, bull_thesis,
                                      our_thesis, bear_thesis, pt_up, pt_wic, pt_down, unaffected_date, expected_close,
                                      m_value, o_value, s_value, a_value, i_value,
                                      c_value, m_overview, o_overview, s_overview, a_overview, i_overview, c_overview,
                                      ticker_hedge_length, request.POST.get('ticker_hedge'), cix_index,
                                      price_target_date, multiples, category, catalyst, deal_type, catalyst_tier,
                                      hedges, gics_sector, lead_analyst, status, pt_up_check, pt_down_check,
                                      pt_wic_check, adjust_based_off, premium_format)

        except Exception as exception:
            print(exception)
            return HttpResponse('Error')

    return HttpResponse(task.id)


def delete_ess_idea(request):
    """
    Delete a ESS IDEA from the Database
    :param request: Request object containing ID of the deal to be deleted
    :return: Appropriate response based on the outcome of the process
    """
    if request.method == 'POST':
        deal_id = request.POST['id']
        response = 'failed'
        try:
            ESS_Idea.objects.filter(id=deal_id).delete()
            response = 'ess_idea_deleted'
        except Exception as exception:
            print(exception)

    return HttpResponse(response)


def ess_idea_download_handler(request):
    """
    Download Handler for ESS IDEA Files
    :param request:
    :return:
    """
    file_path = os.path.join(settings.MEDIA_URL, request.GET['path'])
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file_handle:
            response = HttpResponse(file_handle.read(), content_type="application/liquid")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404('You have not uploaded any File to support this Model!!')

# endregion


# region Credit IDEA Database


def add_new_credit_deal(request):
    """
    Adds a new Credit IDEA Deal
    :param request: Request object containing Credit Deal form fields
    :return: Appropriate string response
    """
    response = 'Failed'
    if request.method == 'POST':
        try:
            deal_name = request.POST['deal_name']
            deal_bucket = request.POST['deal_bucket']
            deal_strategy_type = request.POST['deal_strategy_type']
            catalyst = request.POST['catalyst']
            catalyst_tier = request.POST['catalyst_tier']
            target_security_cusip = request.POST['target_security_cusip']
            coupon = request.POST['coupon']
            hedge_security_cusip = request.POST['hedge_security_cusip']
            estimated_closing_date = request.POST['estimated_closing_date']
            upside_price = request.POST['upside_price']
            downside_price = request.POST['downside_price']

            CreditDatabase(deal_name=deal_name, deal_bucket=deal_bucket, deal_strategy_type=deal_strategy_type,
                           catalyst=catalyst, catalyst_tier=catalyst_tier, target_security_cusip=target_security_cusip,
                           coupon=coupon, hedge_security_cusip=hedge_security_cusip,
                           estimated_close_date=estimated_closing_date, upside_price=upside_price,
                           downside_price=downside_price).save()
            response = 'Success'
        except Exception as exception:
            print(exception)
    return HttpResponse(response)


def delete_credit_deal(request):
    """
    View to delete a Credit deal
    :param request: Request object containing the ID of a credit deal to be deleted.
    :return: Appropriate response based on outcome of the execution
    """
    response = 'Failed'
    if request.method == 'POST':
        try:
            id = request.POST['id']
            CreditDatabase.objects.get(id=id).delete()
            response = 'Success'
        except Exception as exception:
            print(exception)
    return HttpResponse(response)


def show_all_credit_deals(request):
    """
    View to retrieve all credit deals
    :param request: Request object (GET)
    :return: render with context dictionary
    """
    credit_deals_df = CreditDatabase.objects.all()
    return render(request, 'credit_database.html', context={'credit_deals_df': credit_deals_df})


# endregion
