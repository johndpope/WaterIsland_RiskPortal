import sys
import os
import io
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
import django
django.setup()
from django.db import close_old_connections
import pandas as pd
import datetime
from risk.models import ESS_Peers, ESS_Idea, ESS_Idea_Upside_Downside_Change_Records, EssIdeaAdjustmentsInformation, \
    EssBalanceSheets
import bbgclient
import json
from django.conf import settings
import ast
import ess_function


def backfill_ess_idea():
    for name, info in django.db.connections.databases.items():  # Close the DB connections
        django.db.connection.close()
        print('Closing connection: ' + str(name))

    deal_change_log_columns = ['Date', 'Deal Name', 'Old Upside', 'Adjusted Upside', 'Old Downside',
                               'Adjusted Downside', 'Old WIC PT', 'Adjusted WIC PT']
    deal_change_log = pd.DataFrame(columns=deal_change_log_columns)
    unique_deals = ['SERV US Equity', 'CVTA US EQUITY']

    no_adjustments_requested_list = []
    failed_adjustments_list = []
    for each_deal in unique_deals:
        try:
            deal_change_dict = {}
            deal_object = ESS_Idea.objects.filter(alpha_ticker__exact=each_deal).order_by('-version_number').first()
            # Reset Downside Attention
            #deal_object.needs_downside_attention = 0
            deal_ticker = deal_object.alpha_ticker
            print('Processing for IDEA Ticker: ' + str(deal_ticker))
            multiples_dictionary = ast.literal_eval(deal_object.multiples_dictionary)[0]
            multiples_dictionary = {k: float(v) for k, v in multiples_dictionary.items()}
            related_peers = ESS_Peers.objects.select_related().filter(ess_idea_id_id=deal_object.id)
            peers_weights_dictionary = {}

            for eachPeer in related_peers:
                peers_weights_dictionary[eachPeer.ticker] = eachPeer.hedge_weight / 100

            premium_as_percent = None
            if deal_object.premium_format == 'percentage':  # Adjust with Percentage
                premium_as_percent = 'percentage'

            # Process only if Requested

            from datetime import timedelta


            if deal_object.pt_down_check == 'Yes' or deal_object.pt_wic_check == 'Yes' or deal_object.pt_up_check == 'Yes':
                pt_flag, bear_flag, bull_flag = None, None, None
                try:
                    balance_sheet_object = EssBalanceSheets.objects.get(deal_key=deal_object.deal_key)
                    upside_balance_sheet = balance_sheet_object.upside_balance_sheet
                    wic_balance_sheet = balance_sheet_object.wic_balance_sheet
                    downside_balance_sheet = balance_sheet_object.downside_balance_sheet

                    if balance_sheet_object.adjust_up_bs_with_bloomberg == 'No':
                        bull_flag = True
                    if balance_sheet_object.adjust_wic_bs_with_bloomberg == 'No':
                        pt_flag = True
                    if balance_sheet_object.adjust_down_bs_with_bloomberg == 'No':
                        bear_flag = True
                except EssBalanceSheets.DoesNotExist:
                    upside_balance_sheet = None
                    wic_balance_sheet = None
                    downside_balance_sheet = None



                # Execute the following block from Unaffected days till today

                unaff = deal_object.unaffected_date
                next_date = datetime.datetime.strptime("2019-05-08", '%Y-%m-%d').date()
                end_date = datetime.datetime.now().date()
                while next_date < end_date:
                    as_of_date = pd.to_datetime(next_date)
                    next_date += timedelta(days=1)



                    api_host = bbgclient.bbgclient.get_next_available_host()
                    result_dictionary = ess_function.final_df(alpha_ticker=deal_ticker,
                                                      cix_index=deal_object.cix_index,
                                                      unaffectedDt=str(deal_object.unaffected_date),
                                                      expected_close=str(deal_object.expected_close),
                                                      tgtDate=str(deal_object.price_target_date),
                                                      analyst_upside=deal_object.pt_up,
                                                      analyst_downside=deal_object.pt_down,
                                                      analyst_pt_wic=deal_object.pt_wic,
                                                      peers2weight=peers_weights_dictionary,
                                                      metric2weight=multiples_dictionary,
                                                      api_host=api_host, adjustments_df_bear=upside_balance_sheet,
                                                      adjustments_df_bull=downside_balance_sheet,
                                                      adjustments_df_pt=wic_balance_sheet, bull_flag=bull_flag,
                                                      bear_flag=bear_flag, pt_flag=pt_flag,
                                                      f_period="1BF", as_of_dt=as_of_date)

                    df = result_dictionary['Final Results']

                    cix_down_price = df['Down Price (CIX)']
                    cix_up_price = df['Up Price (CIX)']
                    regression_up_price = df['Up Price (Regression)']
                    regression_down_price = df['Down Price (Regression)']
                    pt_wic_price_cix = df['PT WIC Price (CIX)']
                    pt_wic_price_regression = df['PT WIC Price (Regression)']


                    if deal_object.pt_wic_check == 'Yes':
                        # Adjust the PT Wic and Record the change
                        old_pt_wic = deal_object.pt_wic
                        deal_change_dict['Old WIC PT'] = old_pt_wic

                        # Here check if it exceeds the 5% threshold to alert the user
                        if deal_object.how_to_adjust == 'cix':
                            # Check if it exceeds 5% for Cix adjustments
                            new_pt_wic = pt_wic_price_cix

                        else:
                            new_pt_wic = pt_wic_price_regression

                        deal_change_dict['Adjusted WIC PT'] = new_pt_wic

                    if deal_object.pt_up_check == 'Yes':
                        old_pt_up = deal_object.pt_up
                        deal_change_dict['Old Upside'] = old_pt_up

                        if deal_object.how_to_adjust == 'cix':
                            new_upside = cix_up_price
                            # Check if it exceeds 5% for Cix adjustments

                        else:
                            new_upside = regression_up_price

                        deal_change_dict['Adjusted Upside'] = new_upside

                    if deal_object.pt_down_check == 'Yes':
                        old_pt_down = deal_object.pt_down
                        deal_change_dict['Old Downside'] = old_pt_down

                        if deal_object.how_to_adjust == 'cix':
                            new_downside = cix_down_price


                        else:
                            new_downside = regression_down_price

                        deal_change_dict['Adjusted Downside'] = new_downside

                    deal_change_dict['Date'] = as_of_date.strftime("%Y-%m-%d")
                    deal_change_dict['Deal Name'] = deal_ticker
                    deal_change_log = deal_change_log.append(deal_change_dict, ignore_index=True)

                # Export to CSV
                deal_change_log.to_csv('BackFill_ESS_IDEAS.csv')

            else:
                no_adjustments_requested_list += [deal_ticker]
                print('No Adjustments requested for : ' + str(deal_ticker))
        except Exception as e:
            print(e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

            print('Failed Calculating Premium Analysis for : ' + str(deal_ticker))
            failed_adjustments_list += [deal_ticker]
            continue



