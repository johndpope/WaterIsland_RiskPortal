import sys
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
import django
django.setup()
from celery import shared_task
from dateutil import parser
from django.db import close_old_connections
import pandas as pd
import datetime
import requests
from dateutil.relativedelta import relativedelta
import numpy as np
from risk.models import ESS_Peers, ESS_Idea, ESS_Idea_Upside_Downside_Change_Records, ESS_Idea_BearFileUploads, \
    ESS_Idea_BullFileUploads, ESS_Idea_OurFileUploads
import bbgclient
import json
from django.conf import settings
import ast
from django_slack import slack_message
from django.core.mail import EmailMessage
api_host = bbgclient.bbgclient.get_next_available_host()
import ess_function
from django import db
from django.core.exceptions import ObjectDoesNotExist


@shared_task
def premium_analysis_flagger():
    """ Run this task each morning to calculate the Upside/Downside and appropriately flag the
    deals where the upside/downside differs by more than 5% """

    for name, info in django.db.connections.databases.items():  # Close the DB connections
        django.db.connection.close()
        print('Closing connection: ' + str(name))

    deal_change_log_columns = ['Date', 'Deal Name', 'Old Upside', 'Adjusted Upside', 'Old Downside',
                               'Adjusted Downside', 'Old WIC PT', 'Adjusted WIC PT']
    deal_change_log = pd.DataFrame(columns=deal_change_log_columns)
    unique_deals = set(ESS_Idea.objects.all().values_list('alpha_ticker', flat=True))

    for each_deal in unique_deals:
        try:
            deal_change_dict = {}
            deal_object = ESS_Idea.objects.filter(alpha_ticker__exact=each_deal).order_by('-version_number').first()

            # Reset Downside Attention
            deal_object.needs_downside_attention = 0

            print('Processing for IDEA Ticker: ' + str(deal_object.alpha_ticker))
            multiples_dictionary = ast.literal_eval(deal_object.multiples_dictionary)[0]
            multiples_dictionary = {k: float(v) for k, v in multiples_dictionary.items()}
            related_peers = ESS_Peers.objects.select_related().filter(ess_idea_id_id=deal_object.id)
            peers_weights_dictionary = {}

            for eachPeer in related_peers:
                peers_weights_dictionary[eachPeer.ticker] = eachPeer.hedge_weight / 100

            premium_as_percent = None
            if deal_object.premium_format == 'percentage':   # Adjust with Percentage
                premium_as_percent = 'percentage'

            # Process only if Requested

            if deal_object.pt_down_check == 'Yes' or deal_object.pt_wic_check == 'Yes' or deal_object.pt_up_check== 'Yes':

                df = ess_function.final_df(alpha_ticker=deal_object.alpha_ticker, cix_index=deal_object.cix_index,
                                           unaffectedDt=str(deal_object.unaffected_date),
                                           expected_close=str(deal_object.expected_close),
                                           tgtDate=str(deal_object.price_target_date),
                                           analyst_upside=deal_object.pt_up,
                                           analyst_downside=deal_object.pt_down,
                                           analyst_pt_wic=deal_object.pt_wic,
                                           peers2weight=peers_weights_dictionary, metric2weight=multiples_dictionary,
                                           api_host=api_host, adjustments_df_now=deal_object.idea_balance_sheet,
                                           adjustments_df_ptd=deal_object.on_pt_balance_sheet,
                                           premium_as_percent=premium_as_percent,
                                           f_period="1BF")

                cix_down_price = df['Down Price (CIX)']
                cix_up_price = df['Up Price (CIX)']
                regression_up_price = df['Up Price (Regression)']
                regression_down_price = df['Down Price (Regression)']
                pt_wic_price_cix = df['PT WIC Price (CIX)']
                pt_wic_price_regression = df['PT WIC Price (Regression)']

                percentage_change_cix_up = ((cix_up_price - deal_object.pt_up)/cix_up_price) * 100
                percentage_change_cix_down = ((cix_down_price - deal_object.pt_down) / cix_down_price) * 100

                percentage_change_reg_up = ((regression_up_price - deal_object.pt_up) / regression_up_price) * 100
                percentage_change_reg_down = ((regression_down_price - deal_object.pt_down) / regression_down_price) * 100

                percentage_change_pt_wic_cix = ((pt_wic_price_cix - deal_object.pt_wic) / pt_wic_price_cix) * 100
                percentage_change_pt_wic_reg = ((pt_wic_price_regression - deal_object.pt_wic) / pt_wic_price_regression) * 100

                if deal_object.pt_wic_check == 'Yes':
                    # Adjust the PT Wic and Record the change
                    old_pt_wic = deal_object.pt_wic
                    deal_object.pt_wic = pt_wic_price_cix if deal_object.how_to_adjust == 'cix' else pt_wic_price_regression
                    deal_change_dict['Old WIC PT'] = old_pt_wic
                    deal_change_dict['Adjusted WIC PT'] = deal_object.pt_wic
                    # Here check if it exceeds the 5% threshold to alert the user
                    if deal_object.how_to_adjust == 'cix':
                        # Check if it exceeds 5% for Cix adjustments
                        if abs(percentage_change_pt_wic_cix) > 5:
                            deal_object.needs_downside_attention = 1
                    else:
                        if abs(percentage_change_pt_wic_reg) > 5:
                            deal_object.needs_downside_attention = 1

                if deal_object.pt_up_check == 'Yes':
                    old_pt_up = deal_object.pt_up
                    deal_object.pt_up = cix_up_price if deal_object.how_to_adjust == 'cix' else regression_up_price
                    deal_change_dict['Old Upside'] = old_pt_up
                    deal_change_dict['Adjusted Upside'] = deal_object.pt_up
                    if deal_object.how_to_adjust == 'cix':
                        # Check if it exceeds 5% for Cix adjustments
                        if abs(percentage_change_cix_up) > 5:
                            deal_object.needs_downside_attention = 1
                    else:
                        if abs(percentage_change_reg_up) > 5:
                            deal_object.needs_downside_attention = 1

                if deal_object.pt_down_check == 'Yes':
                    old_pt_down = deal_object.pt_down
                    deal_object.pt_down = cix_down_price if deal_object.how_to_adjust == 'cix' else regression_down_price
                    deal_change_dict['Old Downside'] = old_pt_down
                    deal_change_dict['Adjusted Downside'] = deal_object.pt_down
                    if deal_object.how_to_adjust == 'cix':
                        # Check if it exceeds 5% for Cix adjustments
                        if abs(percentage_change_cix_down) > 5:
                            deal_object.needs_downside_attention = 1
                    else:
                        if abs(percentage_change_reg_down) > 5:
                            deal_object.needs_downside_attention = 1

                deal_change_dict['Date'] = datetime.datetime.now().date().strftime("%Y-%m-%d")
                deal_change_dict['Deal Name'] = deal_object.alpha_ticker
                deal_change_log = deal_change_log.append(deal_change_dict, ignore_index=True)
                deal_object.save()
                # Record this Upside downside change for the deal
                ESS_Idea_Upside_Downside_Change_Records(ess_idea_id_id=deal_object.id, deal_key=deal_object.deal_key,
                                                        pt_up=deal_object.pt_up,
                                                        pt_wic=deal_object.pt_wic, pt_down=deal_object.pt_down,
                                                        date_updated=datetime.datetime.now().date()
                                                        .strftime('%Y-%m-%d')).save()

                print('Recorded Upside/Downside Adjustments for ' + str(deal_object.alpha_ticker))
            else:
                print('No Adjustments requested for : ' + str(deal_object.alpha_ticker))
        except Exception as e:
            print(e)
            print('Failed Calculating Premium Analysis for : '+str(deal_object.alpha_ticker))
            continue
    # Todo Email the Dataframe to the ESS Team
    from tabulate import tabulate
    email = EmailMessage('ESS IDEA Database - Adjustments', body=tabulate(deal_change_log,
                                                                          headers=deal_change_log.columns,
                                                                          showindex=False, tablefmt='psql'),
                         to=['risk@wicfunds.com', 'cwatkins@wicfunds.com', 'tchen@wicfunds.com',
                             'kkeung@wicfunds.com'], from_email='dispatch@wicfunds.com')

    email.attach('EssIDEA_Adjustments.csv', deal_change_log.to_csv(), 'text/csv')
    email.send()


@shared_task
def add_new_idea(bull_thesis_model_files, our_thesis_model_files, bear_thesis_model_files, update_id, ticker,
                 situation_overview, company_overview, bull_thesis,
                 our_thesis, bear_thesis, pt_up, pt_wic, pt_down, unaffected_date, expected_close, m_value, o_value,
                 s_value, a_value, i_value,
                 c_value, m_overview, o_overview, s_overview, a_overview, i_overview, c_overview, ticker_hedge_length,
                 ticker_hedge_mappings, cix_index, price_target_date, multiples, category, catalyst, deal_type,
                 catalyst_tier, hedges, gics_sector, lead_analyst, status, pt_up_check, pt_down_check, pt_wic_check,
                 adjust_based_off, premium_format):
    try:
        multiples_mappings = json.loads(multiples)
        # Get it into the right format
        peer_tickers = []
        peer_hedge_weights = []
        ticker_hedge_mappings = json.loads(ticker_hedge_mappings)

        for i in range(int(ticker_hedge_length)):
            # Store Ticker and Hedge Weight in a Dictionary
            p_ticker = ticker_hedge_mappings[i]['ticker'].upper()
            p_ticker = p_ticker + " EQUITY" if "EQUITY" not in p_ticker else p_ticker
            peer_tickers.append(p_ticker)
            peer_hedge_weights.append(ticker_hedge_mappings[i]['hedge'])

        if len(peer_tickers) == 0:
            '''Only calcuate for alphas'''
            print('No peers specified...')
            end_date = datetime.datetime.strptime(unaffected_date, '%Y-%m-%d')
            start_date = end_date - relativedelta(months=3)

            start_date = datetime.datetime.strftime(start_date, "%Y%m%d")

            from datetime import timedelta
            # Reset End Date to Get Prices till date
            end_date = datetime.datetime.today().strftime(
                "%Y%m%d")  # - timedelta(days=3)).strftime("%Y%m%d") #Just for testing daily Calc
            r = requests.get("http://192.168.0.15:8080/wic/api/v1.0/general_histdata",
                             params={'idtype': "tickers", "fields": "PX_LAST",
                                     "tickers": ticker + "," + ','.join(peer_tickers),
                                     "override": "", "start_date": start_date, "end_date": end_date},
                             timeout=15)  # Set a 15 secs Timeout

            print(r.json()['results'])
            ticker_counter = 0
            for every_row in r.json()['results']:
                if ticker in every_row:
                    alpha_prices = r.json()['results'][ticker_counter][ticker]['fields']['PX_LAST']
                    dates_array = r.json()['results'][ticker_counter][ticker]['fields']['date']
                ticker_counter += 1

            alpha_chart = []

            print('Creating Alpha Chart...')
            for price, date in zip(alpha_prices, dates_array):
                alpha_chart.append({
                    "date": date,
                    "px_last": price
                })

            api_host = bbgclient.bbgclient.get_next_available_host()
            alpha_ev_ebitda_chart_ltm = []
            alpha_ev_ebitda_chart_1bf = []
            alpha_ev_ebitda_chart_2bf = []

            alpha_p_fcf_chart = []

            # alpha_prices_dataframe = pd.DataFrame({'Date':dates_array, 'PX_LAST':alpha_prices})

            price = float(alpha_prices[-1])  # Get most Recent Price
            alpha_ev_ebitda_1bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_CUR_EV_TO_EBITDA', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                     datetime.datetime.now().strftime('%Y%m%d'),
                                                                     {'BEST_FPERIOD_OVERRIDE': '1BF'}, api_host)
            alpha_ev_ebitda_2bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_CUR_EV_TO_EBITDA', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                     datetime.datetime.now().strftime('%Y%m%d'),
                                                                     {'BEST_FPERIOD_OVERRIDE': '2BF'}, api_host)
            alpha_ev_ebitda_ltm = bbgclient.bbgclient.get_timeseries(ticker, 'CURRENT_EV_TO_T12M_EBITDA', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                     datetime.datetime.now().strftime('%Y%m%d'), {},
                                                                     api_host)

            for j in range(0, len(alpha_ev_ebitda_1bf)):
                alpha_ev_ebitda_chart_1bf.append({
                    "date": alpha_ev_ebitda_1bf.index[j],
                    "ev_ebitda_value": alpha_ev_ebitda_1bf[j]
                })

            for j in range(0, len(alpha_ev_ebitda_2bf)):
                alpha_ev_ebitda_chart_2bf.append({
                    "date": alpha_ev_ebitda_2bf.index[j],
                    "ev_ebitda_value": alpha_ev_ebitda_2bf[j]
                })

            for j in range(0, len(alpha_ev_ebitda_ltm)):
                alpha_ev_ebitda_chart_ltm.append({
                    "date": alpha_ev_ebitda_ltm.index[j],
                    "ev_ebitda_value": alpha_ev_ebitda_ltm[j]
                })

            alpha_p_eps_chart_ltm = []
            alpha_p_eps_chart_1bf = []
            alpha_p_eps_chart_2bf = []

            alpha_pe_ratio_ltm = bbgclient.bbgclient.get_timeseries(ticker, 'T12M_DIL_PE_CONT_OPS', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                    datetime.datetime.now().strftime('%Y%m%d'), {},
                                                                    api_host)
            alpha_pe_ratio_1bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_PE_RATIO', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                    datetime.datetime.now().strftime('%Y%m%d'),
                                                                    {'BEST_FPERIOD_OVERRIDE': '1BF'}, api_host)
            alpha_pe_ratio_2bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_PE_RATIO', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                    datetime.datetime.now().strftime('%Y%m%d'),
                                                                    {'BEST_FPERIOD_OVERRIDE': '2BF'}, api_host)

            for j in range(0, len(alpha_pe_ratio_ltm)):
                alpha_p_eps_chart_ltm.append({
                    "date": alpha_pe_ratio_ltm.index[j],
                    "pe_ratio": alpha_pe_ratio_ltm[j]
                })

            for j in range(0, len(alpha_pe_ratio_1bf)):
                alpha_p_eps_chart_1bf.append({
                    "date": alpha_pe_ratio_1bf.index[j],
                    "pe_ratio": alpha_pe_ratio_1bf[j]
                })

            for j in range(0, len(alpha_pe_ratio_2bf)):
                alpha_p_eps_chart_2bf.append({
                    "date": alpha_pe_ratio_2bf.index[j],
                    "pe_ratio": alpha_pe_ratio_2bf[j]
                })

            alpha_px_to_fcf = get_fcf_yield(ticker=ticker, start_date_yyyymmdd=(
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                            end_date_yyyymmdd=datetime.datetime.now().strftime('%Y%m%d'),
                                            fperiod='1BF', api_host=api_host)
            for date, p_fcf_value in zip(alpha_px_to_fcf['Date'], alpha_px_to_fcf['FCF yield']):
                alpha_p_fcf_chart.append({
                    "date": date,
                    "p_fcf_value": p_fcf_value
                })

            gross_percentage = (pt_wic / price) - 1

            difference_in_days = (
                    datetime.datetime.date(
                        datetime.datetime.strptime(expected_close, '%Y-%m-%d')) - datetime.datetime.date(
                datetime.datetime.now())).days
            ann_percentage = ((gross_percentage / difference_in_days) * 365)
            theoretical_sharpe = 0
            implied_probability = (price - pt_down) / (pt_up - pt_down)
            implied_probability_chart = []
            event_premium_chart = []
            for date, alpha_price in zip(dates_array, alpha_prices):
                implied_probability_chart.append({
                    "date": date,
                    "implied_probability": float((float(alpha_price) - pt_down) / (pt_up - pt_down))
                })
                event_premium_chart.append({
                    "date": date,
                    "event_premium": float((float(alpha_price) - pt_down) / pt_down)
                })

            event_premium = (price - pt_down) / pt_down
            gross_percentage = str(round(gross_percentage * 100, 2)) + "%"
            ann_percentage = str(round(ann_percentage * 100, 2)) + "%"
            hedged_volatility = str(round(0 * 100, 2)) + "%"
            implied_probability = str(round(implied_probability * 100, 2)) + "%"
            event_premium = str(round(event_premium * 100, 2)) + "%"
            theoretical_sharpe = str(round(theoretical_sharpe, 2))

            # Just save Alpha if No Hedges...
            # Get latest Deal Key
            latest_deal_key = ESS_Idea.objects.latest('deal_key') + 1

            new_deal = ESS_Idea(alpha_ticker=ticker, price=price, pt_up=pt_up, pt_down=pt_down, pt_wic=pt_wic,
                                unaffected_date=unaffected_date, expected_close=expected_close,
                                gross_percentage=gross_percentage, ann_percentage=ann_percentage,
                                hedged_volatility=hedged_volatility, theoretical_sharpe=theoretical_sharpe,
                                implied_probability=implied_probability, event_premium=event_premium,
                                situation_overview=situation_overview, company_overview=company_overview,
                                bull_thesis=bull_thesis, our_thesis=our_thesis, bear_thesis=bear_thesis,
                                m_value=m_value,
                                o_value=o_value, s_value=s_value, a_value=a_value,
                                i_value=i_value, c_value=c_value, m_overview=m_overview, o_overview=o_overview,
                                s_overview=s_overview, a_overview=a_overview,
                                i_overview=i_overview, c_overview=c_overview, alpha_chart=alpha_chart,
                                hedge_chart=[], market_neutral_chart=[],
                                implied_probability_chart=implied_probability_chart,
                                event_premium_chart=event_premium_chart, fcf_yield_chart=json.dumps(alpha_p_fcf_chart),
                                ev_ebitda_chart_ltm=json.dumps(alpha_ev_ebitda_chart_ltm),
                                ev_ebitda_chart_2bf=json.dumps(alpha_ev_ebitda_chart_2bf),
                                ev_ebitda_chart_1bf=json.dumps(alpha_ev_ebitda_chart_1bf),
                                p_eps_chart_ltm=json.dumps(alpha_p_eps_chart_ltm),
                                p_eps_chart_2bf=json.dumps(alpha_p_eps_chart_2bf),
                                p_eps_chart_1bf=json.dumps(alpha_p_eps_chart_1bf),
                                multiples_dictionary=multiples_mappings, price_target_date=price_target_date,
                                cix_index=cix_index, category=category, catalyst=catalyst, deal_type=deal_type,
                                catalyst_tier=catalyst_tier,
                                hedges=hedges, gics_sector=gics_sector, lead_analyst=lead_analyst, status=status,
                                version_number=0, deal_key=latest_deal_key, pt_up_check=pt_up_check,
                                pt_down_check=pt_down_check, pt_wic_check=pt_wic_check, how_to_adjust=
                                adjust_based_off, premium_format=premium_format)
            # Save the Newly created Deal

            new_deal.save()

            print('Saving File Uploads....')

            if bull_thesis_model_files is not None:
                for file in bull_thesis_model_files:
                    ESS_Idea_BullFileUploads(ess_idea_id_id=new_deal.id, deal_key=new_deal.deal_key,
                                             bull_thesis_model=file, uploaded_at=datetime.datetime.now().date()).save()

            if our_thesis_model_files is not None:
                for file in our_thesis_model_files:
                    ESS_Idea_OurFileUploads(ess_idea_id_id=new_deal.id, deal_key=new_deal.deal_key,
                                            our_thesis_model=file, uploaded_at=datetime.datetime.now().date()).save()

            if bear_thesis_model_files is not None:
                for file in bear_thesis_model_files:
                    ESS_Idea_BearFileUploads(ess_idea_id_id=new_deal.id, deal_key=new_deal.deal_key,
                                             bear_thesis_model=file, uploaded_at=datetime.datetime.now().date()).save()





            return 'Task done'

        # -------------- REGION FOR ONLY ALPHA CALCULATION --------------------------------------------------------

        # Stored the Peers and Tickers. Query Bloomberg for the Prices
        end_date = datetime.datetime.strptime(unaffected_date, '%Y-%m-%d')
        start_date = end_date - relativedelta(months=3)

        start_date = datetime.datetime.strftime(start_date, "%Y%m%d")

        from datetime import timedelta
        # Reset End Date to Get Prices till date
        end_date = datetime.datetime.today().strftime(
            "%Y%m%d")  # - timedelta(days=3)).strftime("%Y%m%d") #Just for testing daily Calc
        r = requests.get("http://192.168.0.15:8080/wic/api/v1.0/general_histdata",
                         params={'idtype': "tickers", "fields": "PX_LAST",
                                 "tickers": ticker + "," + ','.join(peer_tickers),
                                 "override": "", "start_date": start_date, "end_date": end_date},
                         timeout=15)  # Set a 15 secs Timeout

        ticker_counter = 0
        for every_row in r.json()['results']:
            if ticker in every_row:
                alpha_prices = r.json()['results'][ticker_counter][ticker]['fields']['PX_LAST']
                dates_array = r.json()['results'][ticker_counter][ticker]['fields']['date']
            ticker_counter += 1

        alpha_chart = []
        for price, date in zip(alpha_prices, dates_array):
            alpha_chart.append({
                "date": date,
                "px_last": price
            })

        # alpha_prices_dataframe = pd.DataFrame({'Date':dates_array, 'PX_LAST':alpha_prices})

        price = float(alpha_prices[-1])  # Get most Recent Price

        peers_data = []  # Array of dictionaries containing Peer name, its historical prices and hedge weight


        for peer_ticker, hedge in zip(peer_tickers, peer_hedge_weights):
            def get_px(peer_ticker):
                historical_prices = []
                ticker_counter = 0
                for every_row in r.json()['results']:
                    if peer_ticker in every_row:
                        historical_prices = r.json()['results'][ticker_counter][peer_ticker]['fields']['PX_LAST']
                    ticker_counter += 1

                return historical_prices

            peers_data.append({'peer': peer_ticker, 'historical_prices': get_px(peer_ticker)
                                  , 'hedge_weight': float(hedge)})


        # Peers data Obtained
        # Calculate peer ratios

        first_price = float(alpha_prices[0])
        ratios = []
        percent_daily_change = []
        for i in range(len(peers_data)):
            # Multiply with hedge weight to calculate ratios
            ratios.append(
                ((first_price * peers_data[i]['hedge_weight']) / float(peers_data[i]['historical_prices'][0])) / 100)

        # Got the Ratios. Now, for remaining Dates, calculate the %change #Ratios represent no. of Shares

        historical_prices_length = 0 if len(peers_data) == 0 else len(peers_data[0]['historical_prices'])

        counter = 0
        hedge_index_change = []

        # Get index of Unaffected Date
        index_of_unaffected_date = 0

        for each_date in dates_array:
            if datetime.datetime.strptime(each_date, '%Y-%m-%d') >= datetime.datetime.strptime(unaffected_date, '%Y-%m-%d'):
                break
            index_of_unaffected_date += 1

        # 2 counters for hedge index changes. Upto Unaffacted Date and one after that

        print('Index of Unaffected Date is: '+ str(index_of_unaffected_date))

        for i in range(0, index_of_unaffected_date):
            changes = []
            while counter < len(ratios) and i<len(peers_data[counter]['historical_prices']):
                if not len(peers_data[counter]['historical_prices']) < historical_prices_length:
                    changes.append(np.multiply(float(peers_data[counter]['historical_prices'][i]), ratios[counter]))

                else:
                    # No prior stock prices available
                    changes.append(np.multiply(0, ratios[counter]))

                counter += 1

            counter = 0
            hedge_index_change.append(np.sum(changes))


        counter = 0


        hedge_index_change.append(
            float(alpha_prices[
                      index_of_unaffected_date]))  # First day will be the same as alpha price (Consider first day Index) #As of the Unaffected Date


        percent_daily_change.append(0)  # first day's change is 0

        for i in range(index_of_unaffected_date + 1, historical_prices_length):
            changes = []
            while counter < len(ratios):
                if not len(peers_data[counter]['historical_prices']) < historical_prices_length:
                    changes.append(np.multiply(float(peers_data[counter]['historical_prices'][i]), ratios[counter]))

                else:
                    # No prior stock prices available
                    changes.append(np.multiply(0, ratios[counter]))

                counter += 1

            counter = 0

            # Subtract Changes from Next Price
            # percent_daily_change.append((next_price - np.sum(changes))/100)
            hedge_index_change.append(np.sum(changes))



        # Toc calculate Hedge Volatility, we take the hedge index changes
        for i in range(1, len(hedge_index_change)):
            yesterdays_price = float(hedge_index_change[i - 1])
            todays_price = float(hedge_index_change[i])
            percentage_change = ((todays_price - yesterdays_price) / yesterdays_price) * 100
            percent_daily_change.append(percentage_change)

        hedge_chart = []
        for change, date in zip(hedge_index_change, dates_array):
            hedge_chart.append({
                "date": date,
                "vol": np.round(float(change), decimals=2)
            })

        # -------- Market Neutral Chart --------------
        # Market Neutral Chart is (Alpha - Hedge) + first_price
        market_neutral_chart = []

        for date, alpha, hedge in zip(dates_array, alpha_prices, hedge_index_change):
            # first_price is price on 0th day
            market_neutral_chart.append({
                "date": date,
                "market_netural_value": np.round((float(alpha) - float(hedge)), decimals=2)
            })

        # ------------------- Save the Ev/Ebitda, P/Eps and P/Fcf charts for Alpha Ticker -------------------
        api_host = bbgclient.bbgclient.get_next_available_host()
        alpha_ev_ebitda_chart_ltm = []
        alpha_ev_ebitda_chart_1bf = []
        alpha_ev_ebitda_chart_2bf = []

        alpha_p_fcf_chart = []

        alpha_ev_ebitda_1bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_CUR_EV_TO_EBITDA', (
                datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                 datetime.datetime.now().strftime('%Y%m%d'),
                                                                 {'BEST_FPERIOD_OVERRIDE': '1BF'}, api_host)
        alpha_ev_ebitda_2bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_CUR_EV_TO_EBITDA', (
                datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                 datetime.datetime.now().strftime('%Y%m%d'),
                                                                 {'BEST_FPERIOD_OVERRIDE': '2BF'}, api_host)
        alpha_ev_ebitda_ltm = bbgclient.bbgclient.get_timeseries(ticker, 'CURRENT_EV_TO_T12M_EBITDA', (
                datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                 datetime.datetime.now().strftime('%Y%m%d'), {},
                                                                 api_host)

        alpha_ev_sales_chart_1bf = []
        alpha_ev_sales_chart_2bf = []
        alpha_ev_sales_chart_ltm = []

        alpha_ev_sales_1bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_CURRENT_EV_BEST_SALES', (
                datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                 datetime.datetime.now().strftime('%Y%m%d'),
                                                                 {'BEST_FPERIOD_OVERRIDE': '1BF'}, api_host)
        alpha_ev_sales_2bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_CURRENT_EV_BEST_SALES', (
                datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                 datetime.datetime.now().strftime('%Y%m%d'),
                                                                 {'BEST_FPERIOD_OVERRIDE': '2BF'}, api_host)
        alpha_ev_sales_ltm = bbgclient.bbgclient.get_timeseries(ticker, 'CURRENT_EV_TO_12M_SALES', (
                datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                 datetime.datetime.now().strftime('%Y%m%d'), {},
                                                                 api_host)

        for j in range(0, len(alpha_ev_ebitda_1bf)):
            alpha_ev_ebitda_chart_1bf.append({
                "date": alpha_ev_ebitda_1bf.index[j],
                "ev_ebitda_value": alpha_ev_ebitda_1bf[j]
            })

        for j in range(0, len(alpha_ev_ebitda_2bf)):
            alpha_ev_ebitda_chart_2bf.append({
                "date": alpha_ev_ebitda_2bf.index[j],
                "ev_ebitda_value": alpha_ev_ebitda_2bf[j]
            })

        for j in range(0, len(alpha_ev_ebitda_ltm)):
            alpha_ev_ebitda_chart_ltm.append({
                "date": alpha_ev_ebitda_ltm.index[j],
                "ev_ebitda_value": alpha_ev_ebitda_ltm[j]
            })

        #  --  Cals for Ev/Sales multiple --

        for j in range(0, len(alpha_ev_sales_1bf)):
            alpha_ev_sales_chart_1bf.append({
                "date": alpha_ev_sales_1bf.index[j],
                "ev_sales_value": alpha_ev_sales_1bf[j]
            })

        for j in range(0, len(alpha_ev_sales_2bf)):
            alpha_ev_sales_chart_2bf.append({
                "date": alpha_ev_sales_2bf.index[j],
                "ev_sales_value": alpha_ev_sales_2bf[j]
            })

        for j in range(0, len(alpha_ev_sales_ltm)):
            alpha_ev_sales_chart_ltm.append({
                "date": alpha_ev_sales_ltm.index[j],
                "ev_sales_value": alpha_ev_sales_ltm[j]
            })


        alpha_p_eps_chart_ltm = []
        alpha_p_eps_chart_1bf = []
        alpha_p_eps_chart_2bf = []

        alpha_pe_ratio_ltm = bbgclient.bbgclient.get_timeseries(ticker, 'T12M_DIL_PE_CONT_OPS', (
                datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                datetime.datetime.now().strftime('%Y%m%d'), {},
                                                                api_host)
        alpha_pe_ratio_1bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_PE_RATIO', (
                datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                datetime.datetime.now().strftime('%Y%m%d'),
                                                                {'BEST_FPERIOD_OVERRIDE': '1BF'}, api_host)
        alpha_pe_ratio_2bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_PE_RATIO', (
                datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                datetime.datetime.now().strftime('%Y%m%d'),
                                                                {'BEST_FPERIOD_OVERRIDE': '2BF'}, api_host)

        for j in range(0, len(alpha_pe_ratio_ltm)):
            alpha_p_eps_chart_ltm.append({
                "date": alpha_pe_ratio_ltm.index[j],
                "pe_ratio": alpha_pe_ratio_ltm[j]
            })

        for j in range(0, len(alpha_pe_ratio_1bf)):
            alpha_p_eps_chart_1bf.append({
                "date": alpha_pe_ratio_1bf.index[j],
                "pe_ratio": alpha_pe_ratio_1bf[j]
            })

        for j in range(0, len(alpha_pe_ratio_2bf)):
            alpha_p_eps_chart_2bf.append({
                "date": alpha_pe_ratio_2bf.index[j],
                "pe_ratio": alpha_pe_ratio_2bf[j]
            })

        alpha_px_to_fcf = get_fcf_yield(ticker=ticker, start_date_yyyymmdd=(
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                        end_date_yyyymmdd=datetime.datetime.now().strftime('%Y%m%d'),
                                        fperiod='1BF', api_host=api_host)
        for date, p_fcf_value in zip(alpha_px_to_fcf['Date'], alpha_px_to_fcf['FCF yield']):
            alpha_p_fcf_chart.append({
                "date": date,
                "p_fcf_value": p_fcf_value
            })

            # ---------------------------------------------------------------------------------------------------

        hedged_volatility = np.std(percent_daily_change) / np.sqrt(252)
        gross_percentage = (pt_wic / price) - 1

        difference_in_days = (
                datetime.datetime.date(datetime.datetime.strptime(expected_close, '%Y-%m-%d')) - datetime.datetime.date(
            datetime.datetime.now())).days
        ann_percentage = ((gross_percentage / difference_in_days) * 365)
        theoretical_sharpe = ann_percentage / hedged_volatility
        implied_probability = (price - pt_down) / (pt_up - pt_down)
        implied_probability_chart = []
        event_premium_chart = []
        for date, alpha_price in zip(dates_array, alpha_prices):
            implied_probability_chart.append({
                "date": date,
                "implied_probability": float((float(alpha_price) - pt_down) / (pt_up - pt_down))
            })
            event_premium_chart.append({
                "date": date,
                "event_premium": float((float(alpha_price) - pt_down) / pt_down)
            })

        event_premium = (price - pt_down) / pt_down
        gross_percentage = str(round(gross_percentage * 100, 2)) + "%"
        ann_percentage = str(round(ann_percentage * 100, 2)) + "%"
        hedged_volatility = str(round(hedged_volatility * 100, 2)) + "%"
        implied_probability = str(round(implied_probability * 100, 2)) + "%"
        event_premium = str(round(event_premium * 100, 2)) + "%"
        theoretical_sharpe = str(round(theoretical_sharpe, 2))

        # Valuation Metrics

        if update_id == 'false':
            try:
                latest_deal_key = ESS_Idea.objects.latest('deal_key').deal_key + 1
            except ObjectDoesNotExist:
                print('Database seems to be empty..')
                latest_deal_key = 0

            #No Update ID means its a New deal to be added....Start with Version Number = 0
            version_number = 0
            new_deal = ESS_Idea(deal_key=latest_deal_key,alpha_ticker=ticker, price=price, pt_up=pt_up, pt_down=pt_down, pt_wic=pt_wic,
                                unaffected_date=unaffected_date, expected_close=expected_close,
                                gross_percentage=gross_percentage, ann_percentage=ann_percentage,
                                hedged_volatility=hedged_volatility, theoretical_sharpe=theoretical_sharpe,
                                implied_probability=implied_probability, event_premium=event_premium,
                                situation_overview=situation_overview, company_overview=company_overview,
                                bull_thesis=bull_thesis, our_thesis=our_thesis, bear_thesis=bear_thesis,
                                m_value=m_value,
                                o_value=o_value, s_value=s_value, a_value=a_value,
                                i_value=i_value, c_value=c_value, m_overview=m_overview, o_overview=o_overview,
                                s_overview=s_overview, a_overview=a_overview,
                                i_overview=i_overview, c_overview=c_overview, alpha_chart=alpha_chart,
                                hedge_chart=hedge_chart, market_neutral_chart=market_neutral_chart,
                                implied_probability_chart=implied_probability_chart,
                                event_premium_chart=event_premium_chart, fcf_yield_chart=json.dumps(alpha_p_fcf_chart),
                                ev_ebitda_chart_ltm=json.dumps(alpha_ev_ebitda_chart_ltm),
                                ev_ebitda_chart_2bf=json.dumps(alpha_ev_ebitda_chart_2bf),
                                ev_ebitda_chart_1bf=json.dumps(alpha_ev_ebitda_chart_1bf),
                                p_eps_chart_ltm=json.dumps(alpha_p_eps_chart_ltm),
                                p_eps_chart_2bf=json.dumps(alpha_p_eps_chart_2bf),
                                p_eps_chart_1bf=json.dumps(alpha_p_eps_chart_1bf),
                                ev_sales_chart_1bf=json.dumps(alpha_ev_sales_chart_1bf),
                                ev_sales_chart_2bf=json.dumps(alpha_ev_sales_chart_2bf),
                                ev_sales_chart_ltm=json.dumps(alpha_ev_sales_chart_ltm),
                                multiples_dictionary=multiples_mappings, cix_index=cix_index,
                                price_target_date=price_target_date, category=category, catalyst=catalyst,
                                deal_type=deal_type, catalyst_tier=catalyst_tier,
                                hedges=hedges, gics_sector=gics_sector, lead_analyst=lead_analyst, status=status,
                                version_number=version_number, pt_up_check=pt_up_check, pt_down_check=pt_down_check,
                                pt_wic_check=pt_wic_check, how_to_adjust=adjust_based_off,
                                premium_format=premium_format)
            # Save the Newly created Deal

            new_deal.save()
            print('Successfully Saved Alpha...')

            print('Now saving, File Uploads...')
            if bull_thesis_model_files is not None:
                for file in bull_thesis_model_files:
                    ESS_Idea_BullFileUploads(ess_idea_id_id=new_deal.id, deal_key=new_deal.deal_key,
                                             bull_thesis_model=file, uploaded_at=datetime.datetime.now().date()).save()

            if our_thesis_model_files is not None:
                for file in our_thesis_model_files:
                    ESS_Idea_OurFileUploads(ess_idea_id_id=new_deal.id, deal_key=new_deal.deal_key,
                                            our_thesis_model=file, uploaded_at=datetime.datetime.now().date()).save()

            if bear_thesis_model_files is not None:
                for file in bear_thesis_model_files:
                    ESS_Idea_BearFileUploads(ess_idea_id_id=new_deal.id, deal_key=new_deal.deal_key,
                                             bear_thesis_model=file, uploaded_at=datetime.datetime.now().date()).save()

        else:
            print('Updating the current IDEA. Creating a new Version ..%%')
            # Just update Existing Model

            # Make sure you append the new chart Data to the existing chart data
            # chart_object = ESS_Idea.objects.get(id=update_id)
            # existing_implied_probability_chart = chart_object.implied_probability_chart
            # existing_implied_probability_chart = eval(
            #     existing_implied_probability_chart)  # Convert String to actual List
            #
            # existing_event_premium_chart = eval(chart_object.event_premium_chart)
            #
            # # Append New Values. Just take the last value in the Arrays and update. Assume, it's always calculated till today. That's why delete the last item only
            #
            # existing_hedge_chart = eval(chart_object.hedge_chart)
            # existing_market_neutral_chart = eval(chart_object.market_neutral_chart)
            # existing_alpha_chart = eval(chart_object.alpha_chart)
            #
            # new_date = dates_array[-1]  # Take the most recent date
            # new_price = alpha_prices[-1]  # Take the most recent price
            #
            # first_price = existing_hedge_chart[-2]['vol']
            #
            # ratios = []
            # for i in range(len(peers_data)):
            #     # Multiply with hedge weight to calculate ratios
            #     ratios.append(((first_price * peers_data[i]['hedge_weight']) / float(
            #         peers_data[i]['historical_prices'][-2])) / 100)
            #
            # counter = 0
            # changes = []
            # while counter < len(ratios):
            #     changes.append(float(peers_data[counter]['historical_prices'][-1]) * ratios[counter])
            #     counter += 1
            #     # Subtract Changes from Next Price
            #     # percent_daily_change.append((next_price - np.sum(changes)) / 100)
            #     # new_hedge_index_change.append(np.sum(changes))
            #
            # del existing_alpha_chart[-1]
            # existing_alpha_chart.append({
            #     'date': new_date,
            #     'px_last': new_price
            # })
            #
            # # Delete the Existing Entry
            # del existing_hedge_chart[-1]
            #
            # existing_hedge_chart.append({
            #     "date": new_date,
            #     "vol": np.sum(changes)
            # })
            #
            # print('Existing Hedge Chart length is..')
            #
            # print(len(existing_hedge_chart))
            #
            # first_price = float(existing_alpha_chart[0]['px_last'])
            #
            # del market_neutral_chart[-1]  # Delete the most Recent Entry
            # market_neutral_chart.append({
            #     "date": new_date,
            #     "market_netural_value": (float(new_price) - float(np.sum(changes))) + first_price
            # })
            #
            # del existing_implied_probability_chart[-1]
            # del existing_event_premium_chart[-1]
            # existing_implied_probability_chart.append({
            #     'date': dates_array[-1],
            #     'implied_probability': float((float(alpha_price) - pt_down) / (pt_up - pt_down))
            # })
            # existing_event_premium_chart.append({
            #     "date": dates_array[-1],
            #     "event_premium": float((float(alpha_price) - pt_down) / pt_down)
            # })

            #Save as a new version

            version_number = int(ESS_Idea.objects.get(id=update_id).version_number) + 1
            latest_deal_key = ESS_Idea.objects.get(id=update_id).deal_key
            print('Recording this Change in Upside/Downside Change records....')
            ESS_Idea_Upside_Downside_Change_Records(ess_idea_id_id=update_id, deal_key=latest_deal_key, pt_up=pt_up,
                                                    pt_wic=pt_wic, pt_down=pt_down,
                                                    date_updated=datetime.datetime.now().date()
                                                    .strftime('%Y-%m-%d')).save()

            print('Printing Version number & Deal Key of current deal..'+str(version_number)
                  + " ->" +str(latest_deal_key))

            new_deal = ESS_Idea(deal_key=latest_deal_key,alpha_ticker=ticker, price=price, pt_up=pt_up, pt_down=pt_down,
                                pt_wic=pt_wic, unaffected_date=unaffected_date, expected_close=expected_close,
                                gross_percentage=gross_percentage, ann_percentage=ann_percentage,
                                hedged_volatility=hedged_volatility, theoretical_sharpe=theoretical_sharpe,
                                implied_probability=implied_probability, event_premium=event_premium,
                                situation_overview=situation_overview, company_overview=company_overview,
                                bull_thesis=bull_thesis, our_thesis=our_thesis, bear_thesis=bear_thesis,
                                m_value=m_value,
                                o_value=o_value, s_value=s_value, a_value=a_value,
                                i_value=i_value, c_value=c_value, m_overview=m_overview, o_overview=o_overview,
                                s_overview=s_overview, a_overview=a_overview,
                                i_overview=i_overview, c_overview=c_overview, alpha_chart=alpha_chart,
                                hedge_chart=hedge_chart, market_neutral_chart=market_neutral_chart,
                                implied_probability_chart=implied_probability_chart,
                                event_premium_chart=event_premium_chart, fcf_yield_chart=json.dumps(alpha_p_fcf_chart),
                                ev_ebitda_chart_ltm=json.dumps(alpha_ev_ebitda_chart_ltm),
                                ev_ebitda_chart_2bf=json.dumps(alpha_ev_ebitda_chart_2bf),
                                ev_ebitda_chart_1bf=json.dumps(alpha_ev_ebitda_chart_1bf),
                                p_eps_chart_ltm=json.dumps(alpha_p_eps_chart_ltm),
                                p_eps_chart_2bf=json.dumps(alpha_p_eps_chart_2bf),
                                p_eps_chart_1bf=json.dumps(alpha_p_eps_chart_1bf),
                                ev_sales_chart_1bf=json.dumps(alpha_ev_sales_chart_1bf),
                                ev_sales_chart_2bf=json.dumps(alpha_ev_sales_chart_2bf),
                                ev_sales_chart_ltm=json.dumps(alpha_ev_sales_chart_ltm),
                                multiples_dictionary=multiples_mappings, cix_index=cix_index,
                                price_target_date=price_target_date, category=category, catalyst=catalyst,
                                deal_type=deal_type, catalyst_tier=catalyst_tier,
                                hedges=hedges, gics_sector=gics_sector, lead_analyst=lead_analyst, status=status,
                                version_number=version_number,  pt_up_check=pt_up_check, pt_down_check=pt_down_check,
                                pt_wic_check=pt_wic_check, how_to_adjust=adjust_based_off,
                                premium_format=premium_format)

            print('Saving New ESS Deal')
            new_deal.save()

            print('Saving File Uploads....')

            if bull_thesis_model_files is not None:
                for file in bull_thesis_model_files:
                    ESS_Idea_BullFileUploads(ess_idea_id_id=new_deal.id, deal_key=new_deal.deal_key,
                                             bull_thesis_model=file, uploaded_at=datetime.datetime.now().date()).save()

            if our_thesis_model_files is not None:
                for file in our_thesis_model_files:
                    ESS_Idea_OurFileUploads(ess_idea_id_id=new_deal.id, deal_key=new_deal.deal_key,
                                            our_thesis_model=file, uploaded_at=datetime.datetime.now().date()).save()

            if bear_thesis_model_files is not None:
                for file in bear_thesis_model_files:
                    ESS_Idea_BearFileUploads(ess_idea_id_id=new_deal.id, deal_key=new_deal.deal_key,
                                             bear_thesis_model=file, uploaded_at=datetime.datetime.now().date()).save()

        # Associate the Deal with each of its Peers
        # First delete existing Peers

        for i in range(len(peers_data)):
            ev_ebitda_1bf = bbgclient.bbgclient.get_timeseries(peers_data[i]['peer'], 'BEST_CUR_EV_TO_EBITDA', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                               datetime.datetime.now().strftime('%Y%m%d'),
                                                               {'BEST_FPERIOD_OVERRIDE': '1BF'}, api_host)
            ev_ebitda_2bf = bbgclient.bbgclient.get_timeseries(peers_data[i]['peer'], 'BEST_CUR_EV_TO_EBITDA', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                               datetime.datetime.now().strftime('%Y%m%d'),
                                                               {'BEST_FPERIOD_OVERRIDE': '2BF'}, api_host)
            ev_ebitda_ltm = bbgclient.bbgclient.get_timeseries(peers_data[i]['peer'], 'CURRENT_EV_TO_T12M_EBITDA', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                               datetime.datetime.now().strftime('%Y%m%d'), {}, api_host)
            ev_ebitda_chart_1bf = []
            ev_ebitda_chart_2bf = []
            ev_ebitda_chart_ltm = []

            for j in range(0, len(ev_ebitda_1bf)):
                ev_ebitda_chart_1bf.append({
                    "date": ev_ebitda_1bf.index[j],
                    "ev_ebitda_value": ev_ebitda_1bf[j]
                })

            for j in range(0, len(ev_ebitda_2bf)):
                ev_ebitda_chart_2bf.append({
                    "date": ev_ebitda_2bf.index[j],
                    "ev_ebitda_value": ev_ebitda_2bf[j]
                })

            for j in range(0, len(ev_ebitda_ltm)):
                ev_ebitda_chart_ltm.append({
                    "date": ev_ebitda_ltm.index[j],
                    "ev_ebitda_value": ev_ebitda_ltm[j]
                })


            # -- Process for EV/Sales Multiple

            ev_sales_1bf = bbgclient.bbgclient.get_timeseries(peers_data[i]['peer'], 'BEST_CURRENT_EV_BEST_SALES', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                               datetime.datetime.now().strftime('%Y%m%d'),
                                                               {'BEST_FPERIOD_OVERRIDE': '1BF'}, api_host)
            ev_sales_2bf = bbgclient.bbgclient.get_timeseries(peers_data[i]['peer'], 'BEST_CURRENT_EV_BEST_SALES', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                               datetime.datetime.now().strftime('%Y%m%d'),
                                                               {'BEST_FPERIOD_OVERRIDE': '2BF'}, api_host)
            ev_sales_ltm = bbgclient.bbgclient.get_timeseries(peers_data[i]['peer'], 'CURRENT_EV_TO_12M_SALES', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                               datetime.datetime.now().strftime('%Y%m%d'), {}, api_host)
            ev_sales_chart_1bf = []
            ev_sales_chart_2bf = []
            ev_sales_chart_ltm = []

            for j in range(0, len(ev_sales_1bf)):
                ev_sales_chart_1bf.append({
                    "date": ev_sales_1bf.index[j],
                    "ev_sales_value": ev_sales_1bf[j]
                })

            for j in range(0, len(ev_sales_2bf)):
                ev_sales_chart_2bf.append({
                    "date": ev_sales_2bf.index[j],
                    "ev_sales_value": ev_sales_2bf[j]
                })

            for j in range(0, len(ev_sales_ltm)):
                ev_sales_chart_ltm.append({
                    "date": ev_sales_ltm.index[j],
                    "ev_sales_value": ev_sales_ltm[j]
                })

            pe_ratio_ltm = bbgclient.bbgclient.get_timeseries(peers_data[i]['peer'], 'T12M_DIL_PE_CONT_OPS',
                                                              (datetime.datetime.now() - relativedelta(
                                                                  months=12)).strftime(
                                                                  '%Y%m%d'), datetime.datetime.now().strftime('%Y%m%d'),
                                                              {},
                                                              api_host)
            pe_ratio_1bf = bbgclient.bbgclient.get_timeseries(peers_data[i]['peer'], 'BEST_PE_RATIO',
                                                              (datetime.datetime.now() - relativedelta(
                                                                  months=12)).strftime(
                                                                  '%Y%m%d'), datetime.datetime.now().strftime('%Y%m%d'),
                                                              {'BEST_FPERIOD_OVERRIDE': '1BF'}, api_host)
            pe_ratio_2bf = bbgclient.bbgclient.get_timeseries(peers_data[i]['peer'], 'BEST_PE_RATIO',
                                                              (datetime.datetime.now() - relativedelta(
                                                                  months=12)).strftime(
                                                                  '%Y%m%d'), datetime.datetime.now().strftime('%Y%m%d'),
                                                              {'BEST_FPERIOD_OVERRIDE': '2BF'}, api_host)

            pe_ratio_chart_ltm = []
            pe_ratio_chart_1bf = []
            pe_ratio_chart_2bf = []

            for j in range(0, len(pe_ratio_ltm)):
                pe_ratio_chart_ltm.append({
                    "date": pe_ratio_ltm.index[j],
                    "pe_ratio": pe_ratio_ltm[j]
                })

            for j in range(0, len(pe_ratio_1bf)):
                pe_ratio_chart_1bf.append({
                    "date": pe_ratio_1bf.index[j],
                    "pe_ratio": pe_ratio_1bf[j]
                })

            for j in range(0, len(pe_ratio_2bf)):
                pe_ratio_chart_2bf.append({
                    "date": pe_ratio_2bf.index[j],
                    "pe_ratio": pe_ratio_2bf[j]
                })

            p_fcf_chart = []
            px_to_fcf = get_fcf_yield(ticker=peers_data[i]['peer'],
                                      start_date_yyyymmdd=(datetime.datetime.now() - relativedelta(months=12)).strftime(
                                          '%Y%m%d'), end_date_yyyymmdd=datetime.datetime.now().strftime('%Y%m%d'),
                                      fperiod='1BF', api_host=api_host)
            for date, p_fcf_value in zip(px_to_fcf['Date'], px_to_fcf['FCF yield']):
                p_fcf_chart.append({
                    "date": date,
                    "p_fcf_value": p_fcf_value
                })

            # Populate the Peer Valuation Table
            name_ev_mkt = bbgclient.bbgclient.get_secid2field([peers_data[i]['peer']], 'tickers',
                                                              ['NAME', 'CURR_ENTP_VAL', 'CUR_MKT_CAP'],
                                                              req_type='refdata',
                                                              api_host=api_host)
            blended_forward_1 = bbgclient.bbgclient.get_secid2field([peers_data[i]['peer']], 'tickers',
                                                                    ['BEST_CUR_EV_TO_EBITDA', 'BEST_PE_RATIO',
                                                                     'BEST_CURRENT_EV_BEST_SALES'
                                                                     ], req_type='refdata',
                                                                    overrides_dict={
                                                                        'BEST_FPERIOD_OVERRIDE': '1BF'},
                                                                    api_host=api_host)

            blended_forward_2 = bbgclient.bbgclient.get_secid2field([peers_data[i]['peer']], 'tickers',
                                                                    ['BEST_CUR_EV_TO_EBITDA', 'BEST_PE_RATIO',
                                                                     'BEST_CURRENT_EV_BEST_SALES'
                                                                     ], req_type='refdata',
                                                                    overrides_dict={
                                                                        'BEST_FPERIOD_OVERRIDE': '2BF'},
                                                                    api_host=api_host)

            peer_company_name = name_ev_mkt[peers_data[i]['peer']]['NAME'].pop() if \
                name_ev_mkt[peers_data[i]['peer']]['NAME'][0] is not None else 'N/A'
            peer_best_ev = name_ev_mkt[peers_data[i]['peer']]['CURR_ENTP_VAL'].pop() if \
                name_ev_mkt[peers_data[i]['peer']]['CURR_ENTP_VAL'][0] is not None else 'N/A'

            peer_cur_market_cap = name_ev_mkt[peers_data[i]['peer']]['CUR_MKT_CAP'].pop() if \
                name_ev_mkt[peers_data[i]['peer']]['CUR_MKT_CAP'][0] is not None else 'N/A'


            peer_ev_sales_bf1 = blended_forward_1[peers_data[i]['peer']]['BEST_CURRENT_EV_BEST_SALES'].pop() if \
                blended_forward_1[peers_data[i]['peer']]['BEST_CURRENT_EV_BEST_SALES'][0] is not None else 'N/A'
            peer_ev_ebitda_bf1 = blended_forward_1[peers_data[i]['peer']]['BEST_CUR_EV_TO_EBITDA'].pop() if \
                blended_forward_1[peers_data[i]['peer']]['BEST_CUR_EV_TO_EBITDA'][0] is not None else 'N/A'
            peer_pe_ratio_bf1 = blended_forward_1[peers_data[i]['peer']]['BEST_PE_RATIO'].pop() if \
                blended_forward_1[peers_data[i]['peer']]['BEST_PE_RATIO'][0] is not None else 'N/A'
            peer_best_calculated_fcf_bf1 = get_fcf_yield(ticker=peers_data[i]['peer'],
                                                         start_date_yyyymmdd=datetime.datetime.today().strftime(
                                                             "%Y%m%d"),
                                                         end_date_yyyymmdd=datetime.datetime.today().strftime("%Y%m%d"),
                                                         api_host=api_host, fperiod='1BF')

            peer_ev_sales_bf2 =  blended_forward_2[peers_data[i]['peer']]['BEST_CURRENT_EV_BEST_SALES'].pop() if \
                blended_forward_2[peers_data[i]['peer']]['BEST_CURRENT_EV_BEST_SALES'][0] is not None else 'N/A'

            peer_ev_ebitda_bf2 = blended_forward_2[peers_data[i]['peer']]['BEST_CUR_EV_TO_EBITDA'].pop() if \
                blended_forward_2[peers_data[i]['peer']]['BEST_CUR_EV_TO_EBITDA'][0] is not None else 'N/A'
            peer_pe_ratio_bf2 = blended_forward_2[peers_data[i]['peer']]['BEST_PE_RATIO'].pop() if \
                blended_forward_2[peers_data[i]['peer']]['BEST_PE_RATIO'][0] is not None else 'N/A'
            peer_best_calculated_fcf_bf2 = get_fcf_yield(ticker=peers_data[i]['peer'],
                                                         start_date_yyyymmdd=datetime.datetime.today().strftime(
                                                             "%Y%m%d"),
                                                         end_date_yyyymmdd=datetime.datetime.today().strftime("%Y%m%d"),
                                                         api_host=api_host, fperiod='2BF')

            peer_best_calculated_fcf_bf1 = round(peer_best_calculated_fcf_bf1['FCF yield'][0] * 100,
                                                 2)  # Auto Handles NaN
            peer_best_calculated_fcf_bf2 = round(peer_best_calculated_fcf_bf2['FCF yield'][0] * 100, 2)

            print('Saving Peer...!!')

            peer = ESS_Peers(name=peer_company_name, enterprise_value=peer_best_ev, market_cap=peer_cur_market_cap,
                             ev_ebitda_bf1=peer_ev_ebitda_bf1,
                             ev_ebitda_bf2=peer_ev_ebitda_bf2,
                             ev_sales_bf1=peer_ev_sales_bf1,
                             ev_sales_bf2=peer_ev_sales_bf2,
                             p_e_bf1=peer_pe_ratio_bf1, p_e_bf2=peer_pe_ratio_bf2,
                             fcf_yield_bf1=peer_best_calculated_fcf_bf1, fcf_yield_bf2=peer_best_calculated_fcf_bf2,
                             ticker=peers_data[i]['peer'], hedge_weight=peers_data[i]['hedge_weight'],
                             p_fcf_chart=json.dumps(p_fcf_chart), ev_ebitda_chart_1bf=json.dumps(ev_ebitda_chart_1bf),
                             ev_ebitda_chart_2bf=json.dumps(ev_ebitda_chart_2bf),
                             ev_ebitda_chart_ltm=json.dumps(ev_ebitda_chart_ltm),
                             ev_sales_chart_ltm=json.dumps(ev_sales_chart_ltm),
                             ev_sales_chart_1bf=json.dumps(ev_sales_chart_1bf),
                             ev_sales_chart_2bf=json.dumps(ev_sales_chart_2bf),
                             p_eps_chart_1bf=json.dumps(pe_ratio_chart_1bf),
                             p_eps_chart_2bf=json.dumps(pe_ratio_chart_2bf),
                             p_eps_chart_ltm=json.dumps(pe_ratio_chart_ltm), version_number=version_number,
                             ess_idea_id_id=new_deal.id)
            peer.save()
            print('Added Peer')

    except Exception as e:
        print(e)
        # slack_message('ESS_IDEA_DATABASE_ERRORS.slack', {'errors': str(e)}, channel='ess_idea_db_errors',
        #               token=settings.SLACK_TOKEN,
        #               name='ESS_IDEA_DB_ERROR_INSPECTOR')
        raise Exception

    # slack_message('ESS_IDEA_DATABASE_ERRORS.slack',
    #               {'errors':'No Errors Detected...Your IDEA Was successfully added (alpha ticker)'+str(ticker)},
    #               channel='ess_idea_db_errors',
    #               token=settings.SLACK_TOKEN,
    #               name='ESS_IDEA_DB_ERROR_INSPECTOR')
    return 'Task Done'


@shared_task
def ess_idea_daily_update():
    """ This is a periodic task that executes every morning at 5. Go through each Deal in ESS Idea Database and
    1. Update Alpha Price with the Last known price
    2. Get the last price of the day and recalculate all the other fields based on that price.
    3. Update all the Charts with the New values """

    # Force a Connection Close to prevent 'My-SQL server has gone away'
    try:
        for name, info in django.db.connections.databases.items():  # Close the DB connections
            django.db.connection.close()
            print('Closing connection: ' + str(name))

        unique_deals = set(ESS_Idea.objects.all().values_list('alpha_ticker', flat=True))
        for eachDealObject in unique_deals:
            eachDealObject = ESS_Idea.objects.filter(alpha_ticker__exact=eachDealObject).order_by('-version_number')\
                .first()

            id = eachDealObject.id
            ticker = eachDealObject.alpha_ticker
            price = eachDealObject.price
            pt_up = eachDealObject.pt_up
            pt_wic = eachDealObject.pt_wic
            pt_down = eachDealObject.pt_down
            unaffected_date = eachDealObject.unaffected_date
            expected_close = eachDealObject.expected_close
            existing_alpha_chart = eachDealObject.alpha_chart
            existing_implied_probability_chart = eachDealObject.implied_probability_chart
            existing_event_premium_chart = eachDealObject.event_premium_chart
            existing_hedge_chart = eachDealObject.hedge_chart
            existing_market_neutral_chart = eachDealObject.market_neutral_chart
            # Make a Request for Yesterday
            peer_tickers = []

            related_peers = ESS_Peers.objects.select_related().filter(ess_idea_id_id=id).values_list()

            related_peers_list = ESS_Peers.objects.select_related().filter(ess_idea_id_id=id)

            # < QuerySet[(300, 'IBM US EQUITY', 30.0), (301, 'AAPL US EQUITY', 10.0), (302, 'QCOM US EQUITY', 10.0), (
            # 303, 'NFLX US EQUITY', 50.0)] >
            print('Processing Daily Update for Deal: '+ str(ticker))
            peer_weights = []

            for i in range(len(related_peers)):
                peer_tickers.append(related_peers[i][2])
                peer_weights.append(related_peers[i][3])

            hedge_weight_dictionary = {}
            for i in range(len(peer_tickers)):
                hedge_weight_dictionary[peer_tickers[i]] = peer_weights[i]

            end_date = unaffected_date.strftime("%Y%m%d")
            start_date = parser.parse(end_date) - relativedelta(months=3)

            start_date = datetime.datetime.strftime(start_date, "%Y%m%d")

            # Reset End Date to Get Prices till date
            end_date = datetime.datetime.today()
            end_date = datetime.datetime.strftime(end_date, "%Y%m%d")

            r = requests.get("http://192.168.0.15:8080/wic/api/v1.0/general_histdata",
                             params={'idtype': "tickers", "fields": "PX_LAST",
                                     "tickers": ticker + "," + ','.join(peer_tickers),
                                     "override": "", "start_date": start_date, "end_date": end_date},
                             timeout=15)  # Set a 15 secs Timeout

            resp = r.json()['results']

            peers_data = []  # Array of dictionaries containing Peer name, its historical prices and hedge weight
            for i in range(len(resp)):
                key = list(resp[i].keys())[0]
                if key == ticker:
                    # append to alpha tickers
                    alpha_prices = resp[i][key]['fields']['PX_LAST']
                    dates_array = resp[i][key]['fields']['date']
                else:
                    peers_data.append({
                        'peer': key,
                        'historical_prices': resp[i][key]['fields']['PX_LAST'],
                        'hedge_weight': hedge_weight_dictionary[key]
                    })


            # Recalculalte Alpha Chart, Hedge Chart & Market Netural Charts Each day. Only Append to Event Premium and Implied Probability

            price = float(alpha_prices[-1])  # Get most Recent Price

            # Calculate peer ratios

            first_price = float(alpha_prices[0])
            ratios = []
            percent_daily_change = []
            for i in range(len(peers_data)):
                # Multiply with hedge weight to calculate ratios
                ratios.append(
                    ((first_price * peers_data[i]['hedge_weight']) / float(
                        peers_data[i]['historical_prices'][0])) / 100)

            # Got the Ratios. Now, for remaining Dates, calculate the %change #Ratios represent no. of Shares

            historical_prices_length = len(peers_data[0]['historical_prices'])

            counter = 0
            # First day will be the same as alpha price (Consider first day Index)
            hedge_index_change = [float(alpha_prices[0])]

            percent_daily_change.append(0)  # first day's change is 0

            #Todo What happens if Peers Data Prices length is > alpha or vice versa?. ALpha opened today but peers 2mbck
            for i in range(1, historical_prices_length):
                next_price = 0
                if i<len(alpha_prices):
                    next_price = float(alpha_prices[i])
                changes = []

                while counter < len(ratios):
                    hp = 0
                    if i >= len(peers_data[counter]['historical_prices']):
                        hp = 0
                    else:
                        hp = float(peers_data[counter]['historical_prices'][i])
                    changes.append(hp * ratios[counter])
                    counter += 1

                counter = 0
                # Subtract Changes from Next Price
                percent_daily_change.append((next_price - np.sum(changes)) / 100)
                hedge_index_change.append(np.sum(changes))

            # Toc calculate Hedge Volatility, we take the hedge index changes
            for i in range(1, len(hedge_index_change)):
                yesterdays_price = float(hedge_index_change[i - 1])
                todays_price = float(hedge_index_change[i])
                percentage_change = ((todays_price - yesterdays_price) / yesterdays_price) * 100
                percent_daily_change.append(percentage_change)

            # -------- Market Neutral Chart --------------
            # Market Neutral Chart is (Alpha - Hedge) + first_price
            # ------------------- Save the Ev/Ebitda, P/Eps and P/Fcf charts for Alpha Ticker -------------------
            api_host = bbgclient.bbgclient.get_next_available_host()
            alpha_ev_ebitda_chart_ltm = []
            alpha_ev_ebitda_chart_1bf = []
            alpha_ev_ebitda_chart_2bf = []

            alpha_p_fcf_chart = []

            alpha_ev_ebitda_1bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_CUR_EV_TO_EBITDA', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                     datetime.datetime.now().strftime('%Y%m%d'),
                                                                     {'BEST_FPERIOD_OVERRIDE': '1BF'}, api_host)
            alpha_ev_ebitda_2bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_CUR_EV_TO_EBITDA', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                     datetime.datetime.now().strftime('%Y%m%d'),
                                                                     {'BEST_FPERIOD_OVERRIDE': '2BF'}, api_host)
            alpha_ev_ebitda_ltm = bbgclient.bbgclient.get_timeseries(ticker, 'CURRENT_EV_TO_T12M_EBITDA', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                     datetime.datetime.now().strftime('%Y%m%d'), {},
                                                                     api_host)

            for j in range(0, len(alpha_ev_ebitda_1bf)):
                alpha_ev_ebitda_chart_1bf.append({
                    "date": alpha_ev_ebitda_1bf.index[j],
                    "ev_ebitda_value": alpha_ev_ebitda_1bf[j]
                })

            for j in range(0, len(alpha_ev_ebitda_2bf)):
                alpha_ev_ebitda_chart_2bf.append({
                    "date": alpha_ev_ebitda_2bf.index[j],
                    "ev_ebitda_value": alpha_ev_ebitda_2bf[j]
                })

            for j in range(0, len(alpha_ev_ebitda_ltm)):
                alpha_ev_ebitda_chart_ltm.append({
                    "date": alpha_ev_ebitda_ltm.index[j],
                    "ev_ebitda_value": alpha_ev_ebitda_ltm[j]
                })

            alpha_p_eps_chart_ltm = []
            alpha_p_eps_chart_1bf = []
            alpha_p_eps_chart_2bf = []

            alpha_pe_ratio_ltm = bbgclient.bbgclient.get_timeseries(ticker, 'T12M_DIL_PE_CONT_OPS', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                    datetime.datetime.now().strftime('%Y%m%d'), {},
                                                                    api_host)
            alpha_pe_ratio_1bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_PE_RATIO', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                    datetime.datetime.now().strftime('%Y%m%d'),
                                                                    {'BEST_FPERIOD_OVERRIDE': '1BF'}, api_host)
            alpha_pe_ratio_2bf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_PE_RATIO', (
                    datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                    datetime.datetime.now().strftime('%Y%m%d'),
                                                                    {'BEST_FPERIOD_OVERRIDE': '2BF'}, api_host)

            for j in range(0, len(alpha_pe_ratio_ltm)):
                alpha_p_eps_chart_ltm.append({
                    "date": alpha_pe_ratio_ltm.index[j],
                    "pe_ratio": alpha_pe_ratio_ltm[j]
                })

            for j in range(0, len(alpha_pe_ratio_1bf)):
                alpha_p_eps_chart_1bf.append({
                    "date": alpha_pe_ratio_1bf.index[j],
                    "pe_ratio": alpha_pe_ratio_1bf[j]
                })

            for j in range(0, len(alpha_pe_ratio_2bf)):
                alpha_p_eps_chart_2bf.append({
                    "date": alpha_pe_ratio_2bf.index[j],
                    "pe_ratio": alpha_pe_ratio_2bf[j]
                })

            alpha_px_to_fcf = get_fcf_yield(ticker=ticker, start_date_yyyymmdd=(
                        datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                            end_date_yyyymmdd=datetime.datetime.now().strftime('%Y%m%d'),
                                            fperiod='1BF', api_host=api_host)
            for date, p_fcf_value in zip(alpha_px_to_fcf['Date'], alpha_px_to_fcf['FCF yield']):
                alpha_p_fcf_chart.append({
                    "date": date,
                    "p_fcf_value": p_fcf_value
                })

                # ---------------------------------------------------------------------------------------------------

            hedged_volatility = np.std(percent_daily_change) / np.sqrt(252)
            gross_percentage = float(pt_wic / price) - 1
            difference_in_days = (expected_close - datetime.datetime.date(datetime.datetime.now())).days

            ann_percentage = float(((gross_percentage / difference_in_days) * 365))
            theoretical_sharpe = ann_percentage / hedged_volatility
            implied_probability = float((price - pt_down) / (pt_up - pt_down))
            existing_implied_probability_chart = eval(existing_implied_probability_chart)
            existing_event_premium_chart = eval(existing_event_premium_chart)
            # Only Append the New Values for Implied Probability and Event Premium

            # Get new dates and new prices
            new_dates = []
            new_prices = []

            for i in range(len(eval(existing_alpha_chart)), len(alpha_prices)):
                new_dates.append(dates_array[i])
                new_prices.append(alpha_prices[i])

            print(new_dates)
            print(new_prices)
            # Append to Existing Hedge Chart
            existing_alpha_chart = eval(existing_alpha_chart)
            for new_date, new_px_last in zip(new_dates, new_prices):
                existing_alpha_chart.append({
                    'date': new_date,
                    'px_last': new_px_last
                })

            existing_hedge_chart = eval(existing_hedge_chart)
            existing_market_neutral_chart = eval(existing_market_neutral_chart)
            ratios = []
            percent_daily_change = []
            for i in range(len(peers_data)):
                # Multiply with hedge weight to calculate ratios
                ratios.append(
                    ((first_price * peers_data[i]['hedge_weight']) / float(
                        peers_data[i]['historical_prices'][0])) / 100)

            # Again calculate the no. of shares
            new_hedge_index_change = []  # Represents how the hedge index has changed for new data
            counter = 0

            for i in range(len(existing_hedge_chart), len(alpha_prices)):
                changes = []
                while counter < len(ratios):
                    hp = 0
                    if i >= len(peers_data[counter]['historical_prices']):
                        hp = 0
                    else:
                        hp = float(peers_data[counter]['historical_prices'][i])

                    changes.append(np.multiply(hp, ratios[counter]))
                    counter += 1
                counter = 0
                # Subtract Changes from Next Price
                new_hedge_index_change.append(np.sum(changes))

            for change, date in zip(new_hedge_index_change, new_dates):
                existing_hedge_chart.append({
                    "date": date,
                    "vol": float(change)
                })

            for date, alpha_price in zip(new_dates, new_prices):
                existing_implied_probability_chart.append({
                    "date": date,
                    "implied_probability": float((float(alpha_price) - pt_down) / (pt_up - pt_down))
                })
                existing_event_premium_chart.append({
                    "date": date,
                    "event_premium": float((float(alpha_price) - pt_down) / pt_down)
                })

            for date, alpha, hedge in zip(new_dates, new_prices, new_hedge_index_change):
                # first_price is price on 0th day
                existing_market_neutral_chart.append({
                    "date": date,
                    "market_netural_value": (float(alpha) - float(hedge))
                })

            event_premium = (price - pt_down) / pt_down

            gross_percentage = str(round(gross_percentage * 100, 2)) + "%"
            ann_percentage = str(round(ann_percentage * 100, 2)) + "%"
            hedged_volatility = str(round(hedged_volatility * 100, 2)) + "%"
            implied_probability = str(round(implied_probability * 100, 2)) + "%"
            event_premium = str(round(event_premium * 100, 2)) + "%"
            theoretical_sharpe = str(round(theoretical_sharpe, 2))

            # Save this to the Database
            ESS_Idea.objects.filter(id=id).update(alpha_ticker=ticker, price=price, pt_up=np.round(float(pt_up),
                                                                                                   decimals=2),
                                                  pt_down=np.round(float(pt_down), decimals=2),
                                                  pt_wic=np.round(float(pt_wic), decimals=2),
                                                  unaffected_date=unaffected_date,
                                                  expected_close=expected_close,
                                                  gross_percentage=gross_percentage, ann_percentage=ann_percentage,
                                                  hedged_volatility=hedged_volatility,
                                                  theoretical_sharpe=theoretical_sharpe,
                                                  implied_probability=implied_probability, event_premium=event_premium,
                                                  alpha_chart=existing_alpha_chart, hedge_chart=existing_hedge_chart,
                                                  market_neutral_chart=existing_market_neutral_chart,
                                                  implied_probability_chart=existing_implied_probability_chart,
                                                  event_premium_chart=existing_event_premium_chart,
                                                  fcf_yield_chart=json.dumps(alpha_p_fcf_chart),
                                                  ev_ebitda_chart_ltm=json.dumps(alpha_ev_ebitda_chart_ltm),
                                                  ev_ebitda_chart_2bf=json.dumps(alpha_ev_ebitda_chart_2bf),
                                                  ev_ebitda_chart_1bf=json.dumps(alpha_ev_ebitda_chart_1bf),
                                                  p_eps_chart_ltm=json.dumps(alpha_p_eps_chart_ltm),
                                                  p_eps_chart_2bf=json.dumps(alpha_p_eps_chart_2bf),
                                                  p_eps_chart_1bf=json.dumps(alpha_p_eps_chart_1bf))

            print(str(id) + ' - Deal Updates. Total newly inserted dates: ' + str(len(new_prices)))

            print('Updating Peer Valuation Metrics....')
            # -------------- UPDATE THE PEERS WITH NEW CHARTS/VALUATION METRICS ------------------------------------
            for every_peer in related_peers_list:
                print('Processing Peer: ' + every_peer.ticker)
                ev_ebitda_1bf = bbgclient.bbgclient.get_timeseries(every_peer.ticker, 'BEST_CUR_EV_TO_EBITDA', (
                        datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                   datetime.datetime.now().strftime('%Y%m%d'),
                                                                   {'BEST_FPERIOD_OVERRIDE': '1BF'}, api_host)
                ev_ebitda_2bf = bbgclient.bbgclient.get_timeseries(every_peer.ticker, 'BEST_CUR_EV_TO_EBITDA', (
                        datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                   datetime.datetime.now().strftime('%Y%m%d'),
                                                                   {'BEST_FPERIOD_OVERRIDE': '2BF'}, api_host)
                ev_ebitda_ltm = bbgclient.bbgclient.get_timeseries(every_peer.ticker, 'CURRENT_EV_TO_T12M_EBITDA', (
                        datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                                                   datetime.datetime.now().strftime('%Y%m%d'), {},
                                                                   api_host)
                ev_ebitda_chart_1bf = []
                ev_ebitda_chart_2bf = []
                ev_ebitda_chart_ltm = []

                for j in range(0, len(ev_ebitda_1bf)):
                    ev_ebitda_chart_1bf.append({
                        "date": ev_ebitda_1bf.index[j],
                        "ev_ebitda_value": ev_ebitda_1bf[j]
                    })

                for j in range(0, len(ev_ebitda_2bf)):
                    ev_ebitda_chart_2bf.append({
                        "date": ev_ebitda_2bf.index[j],
                        "ev_ebitda_value": ev_ebitda_2bf[j]
                    })

                for j in range(0, len(ev_ebitda_ltm)):
                    ev_ebitda_chart_ltm.append({
                        "date": ev_ebitda_ltm.index[j],
                        "ev_ebitda_value": ev_ebitda_ltm[j]
                    })

                pe_ratio_ltm = bbgclient.bbgclient.get_timeseries(every_peer.ticker, 'T12M_DIL_PE_CONT_OPS',
                                                                  (datetime.datetime.now() - relativedelta(
                                                                      months=12)).strftime(
                                                                      '%Y%m%d'),
                                                                  datetime.datetime.now().strftime('%Y%m%d'), {},
                                                                  api_host)
                pe_ratio_1bf = bbgclient.bbgclient.get_timeseries(every_peer.ticker, 'BEST_PE_RATIO',
                                                                  (datetime.datetime.now() - relativedelta(
                                                                      months=12)).strftime(
                                                                      '%Y%m%d'),
                                                                  datetime.datetime.now().strftime('%Y%m%d'),
                                                                  {'BEST_FPERIOD_OVERRIDE': '1BF'}, api_host)
                pe_ratio_2bf = bbgclient.bbgclient.get_timeseries(every_peer.ticker, 'BEST_PE_RATIO',
                                                                  (datetime.datetime.now() - relativedelta(
                                                                      months=12)).strftime(
                                                                      '%Y%m%d'),
                                                                  datetime.datetime.now().strftime('%Y%m%d'),
                                                                  {'BEST_FPERIOD_OVERRIDE': '2BF'}, api_host)

                pe_ratio_chart_ltm = []
                pe_ratio_chart_1bf = []
                pe_ratio_chart_2bf = []

                for j in range(0, len(pe_ratio_ltm)):
                    pe_ratio_chart_ltm.append({
                        "date": pe_ratio_ltm.index[j],
                        "pe_ratio": pe_ratio_ltm[j]
                    })

                for j in range(0, len(pe_ratio_1bf)):
                    pe_ratio_chart_1bf.append({
                        "date": pe_ratio_1bf.index[j],
                        "pe_ratio": pe_ratio_1bf[j]
                    })

                for j in range(0, len(pe_ratio_2bf)):
                    pe_ratio_chart_2bf.append({
                        "date": pe_ratio_2bf.index[j],
                        "pe_ratio": pe_ratio_2bf[j]
                    })

                p_fcf_chart = []
                px_to_fcf = get_fcf_yield(ticker=every_peer.ticker, start_date_yyyymmdd=(
                            datetime.datetime.now() - relativedelta(months=12)).strftime('%Y%m%d'),
                                          end_date_yyyymmdd=datetime.datetime.now().strftime('%Y%m%d'), fperiod='1BF',
                                          api_host=api_host)
                for date, p_fcf_value in zip(px_to_fcf['Date'], px_to_fcf['FCF yield']):
                    p_fcf_chart.append({
                        "date": date,
                        "p_fcf_value": p_fcf_value
                    })

                # Populate the Peer Valuation Table
                name_ev_mkt = bbgclient.bbgclient.get_secid2field([every_peer.ticker], 'tickers',
                                                                  ['NAME', 'CURR_ENTP_VAL', 'CUR_MKT_CAP'],
                                                                  req_type='refdata',
                                                                  api_host=api_host)
                blended_forward_1 = bbgclient.bbgclient.get_secid2field([every_peer.ticker], 'tickers',
                                                                        ['BEST_CUR_EV_TO_EBITDA', 'BEST_PE_RATIO'],
                                                                        req_type='refdata',
                                                                        overrides_dict={
                                                                            'BEST_FPERIOD_OVERRIDE': '1BF'},
                                                                        api_host=api_host)

                blended_forward_2 = bbgclient.bbgclient.get_secid2field([every_peer.ticker], 'tickers',
                                                                        ['BEST_CUR_EV_TO_EBITDA', 'BEST_PE_RATIO'],
                                                                        req_type='refdata',
                                                                        overrides_dict={
                                                                            'BEST_FPERIOD_OVERRIDE': '2BF'},
                                                                        api_host=api_host)

                peer_company_name = name_ev_mkt[every_peer.ticker]['NAME'].pop() if \
                    name_ev_mkt[every_peer.ticker]['NAME'][0] != None else 'N/A'
                peer_best_ev = name_ev_mkt[every_peer.ticker]['CURR_ENTP_VAL'].pop() if \
                    name_ev_mkt[every_peer.ticker]['CURR_ENTP_VAL'][0] != None else 'N/A'

                peer_cur_market_cap = name_ev_mkt[every_peer.ticker]['CUR_MKT_CAP'].pop() if \
                    name_ev_mkt[every_peer.ticker]['CUR_MKT_CAP'][0] != None else 'N/A'

                peer_ev_ebitda_bf1 = blended_forward_1[every_peer.ticker]['BEST_CUR_EV_TO_EBITDA'].pop() if \
                    blended_forward_1[every_peer.ticker]['BEST_CUR_EV_TO_EBITDA'][0] != None else 'N/A'
                peer_pe_ratio_bf1 = blended_forward_1[every_peer.ticker]['BEST_PE_RATIO'].pop() if \
                    blended_forward_1[every_peer.ticker]['BEST_PE_RATIO'][0] != None else 'N/A'
                peer_best_calculated_fcf_bf1 = get_fcf_yield(ticker=every_peer.ticker,
                                                             start_date_yyyymmdd=datetime.datetime.today().strftime(
                                                                 "%Y%m%d"),
                                                             end_date_yyyymmdd=datetime.datetime.today().strftime(
                                                                 "%Y%m%d"),
                                                             api_host=api_host, fperiod='1BF')

                peer_ev_ebitda_bf2 = blended_forward_2[every_peer.ticker]['BEST_CUR_EV_TO_EBITDA'].pop() if \
                    blended_forward_2[every_peer.ticker]['BEST_CUR_EV_TO_EBITDA'][0] != None else 'N/A'
                peer_pe_ratio_bf2 = blended_forward_2[every_peer.ticker]['BEST_PE_RATIO'].pop() if \
                    blended_forward_2[every_peer.ticker]['BEST_PE_RATIO'][0] != None else 'N/A'
                peer_best_calculated_fcf_bf2 = get_fcf_yield(ticker=every_peer.ticker,
                                                             start_date_yyyymmdd=datetime.datetime.today().strftime(
                                                                 "%Y%m%d"),
                                                             end_date_yyyymmdd=datetime.datetime.today().strftime(
                                                                 "%Y%m%d"),
                                                             api_host=api_host, fperiod='2BF')

                peer_best_calculated_fcf_bf1 = round(peer_best_calculated_fcf_bf1['FCF yield'][0] * 100,
                                                     2)  # Auto Handles NaN
                peer_best_calculated_fcf_bf2 = round(peer_best_calculated_fcf_bf2['FCF yield'][0] * 100, 2)

                ESS_Peers.objects.filter(id=every_peer.id).update(name=peer_company_name, enterprise_value=peer_best_ev,
                                                                  market_cap=peer_cur_market_cap,
                                                                  ev_ebitda_bf1=peer_ev_ebitda_bf1,
                                                                  ev_ebitda_bf2=peer_ev_ebitda_bf2,
                                                                  p_e_bf1=peer_pe_ratio_bf1, p_e_bf2=peer_pe_ratio_bf2,
                                                                  fcf_yield_bf1=peer_best_calculated_fcf_bf1,
                                                                  fcf_yield_bf2=peer_best_calculated_fcf_bf2,
                                                                  ticker=every_peer.ticker,
                                                                  hedge_weight=every_peer.hedge_weight,
                                                                  p_fcf_chart=json.dumps(p_fcf_chart),
                                                                  ev_ebitda_chart_1bf=json.dumps(ev_ebitda_chart_1bf),
                                                                  ev_ebitda_chart_2bf=json.dumps(ev_ebitda_chart_2bf),
                                                                  ev_ebitda_chart_ltm=json.dumps(ev_ebitda_chart_ltm),
                                                                  p_eps_chart_1bf=json.dumps(pe_ratio_chart_1bf),
                                                                  p_eps_chart_2bf=json.dumps(pe_ratio_chart_2bf),
                                                                  p_eps_chart_ltm=json.dumps(pe_ratio_chart_ltm))
                print(str(every_peer.id) + " Peer ID Updated!")
                # peer.save()
            # --------------------------------------------------------------------------------------------------------
            print('Peers Updated....')

    except Exception as e:
        # slack_message('ESS_IDEA_DATABASE_ERRORS.slack', {'errors': str(e)}, channel='ess_idea_db_errors',
        #               token=settings.SLACK_TOKEN)
        print('Exception in Celery Task' + str(e))
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)


def get_fcf_yield(ticker, api_host, start_date_yyyymmdd, end_date_yyyymmdd, fperiod):
    ''' Calculates FCF Yield and Returns a Series object '''
    px = bbgclient.bbgclient.get_timeseries(ticker, 'PX_LAST', start_date_yyyymmdd, end_date_yyyymmdd,
                                            api_host=api_host).reset_index().rename(columns={'index': 'Date', 0: 'PX'})

    best_estimate_fcf = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_ESTIMATE_FCF', start_date_yyyymmdd,
                                                           end_date_yyyymmdd, {'BEST_FPERIOD_OVERRIDE': fperiod},
                                                           api_host).reset_index().rename(
        columns={'index': 'Date', 0: 'BEST_ESTIMATE_FCF'})

    ni = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_NET_INCOME', start_date_yyyymmdd, end_date_yyyymmdd,
                                            {'BEST_FPERIOD_OVERRIDE': fperiod}, api_host).reset_index().rename(
        columns={'index': 'Date', 0: 'NI'})

    eps = bbgclient.bbgclient.get_timeseries(ticker, 'BEST_EPS', start_date_yyyymmdd, end_date_yyyymmdd,
                                             {'BEST_FPERIOD_OVERRIDE': fperiod}, api_host).reset_index().rename(
        columns={'index': 'Date', 0: 'EPS'})


    fcf = pd.merge(px, best_estimate_fcf, how='left', on=['Date']).ffill().bfill()
    fcf = pd.merge(fcf, ni, how='left', on=['Date']).ffill().bfill()
    fcf = pd.merge(fcf, eps, how='left', on=['Date']).ffill().bfill()

    fcf['FCF'] = (fcf['BEST_ESTIMATE_FCF']) / (fcf['NI'] / fcf['EPS'])
    if 'LN EQUITY' in ticker.upper() or 'SJ EQUITY' in ticker.upper():
        #Money in Pence for UK stock...Divide by 100
        fcf['PX'] = fcf['PX']/100
    fcf['FCF yield'] = fcf['FCF'] / fcf['PX']

    return fcf[['Date', 'FCF yield']]
