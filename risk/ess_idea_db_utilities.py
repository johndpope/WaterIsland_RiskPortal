import datetime
from dateutil.relativedelta import relativedelta
import requests
import pandas as pd
import bbgclient
import numpy as np
import json
from .models import *
from django.db import transaction
from django.db.models import Max


def add_new_deal(bull_thesis_model_files, our_thesis_model_files, bear_thesis_model_files, update_id,
                 ticker,
                 situation_overview, company_overview, bull_thesis,
                 our_thesis, bear_thesis, pt_up, pt_wic, pt_down, unaffected_date, expected_close,
                 m_value, o_value,
                 s_value, a_value, i_value,
                 c_value, m_overview, o_overview, s_overview, a_overview, i_overview, c_overview,
                 ticker_hedge_length,
                 ticker_hedge_mappings, cix_index, price_target_date, multiples, category, catalyst,
                 deal_type,
                 catalyst_tier, hedges, gics_sector, lead_analyst, status, pt_up_check,
                 pt_down_check, pt_wic_check,
                 adjust_based_off, premium_format, multiples_mappings, progress_recorder, latest_deal_key, peer_tickers, peer_hedge_weights):
    """ Function to calculate parameters to add a new deal """
    # Stored the Peers and Tickers. Query Bloomberg for the Prices
    end_date = datetime.datetime.strptime(unaffected_date, '%Y-%m-%d')
    start_date = end_date - relativedelta(months=3)

    start_date = datetime.datetime.strftime(start_date, "%Y%m%d")
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
        if datetime.datetime.strptime(each_date, '%Y-%m-%d') >= datetime.datetime.strptime(unaffected_date,
                                                                                           '%Y-%m-%d'):
            break
        index_of_unaffected_date += 1

    # 2 counters for hedge index changes. Upto Unaffacted Date and one after that
    progress_recorder.set_progress(60, 100)
    print('Index of Unaffected Date is: ' + str(index_of_unaffected_date))

    for i in range(0, index_of_unaffected_date):
        changes = []
        while counter < len(ratios) and i < len(peers_data[counter]['historical_prices']):
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
    progress_recorder.set_progress(70, 100)
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

    progress_recorder.set_progress(75, 100)
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

    progress_recorder.set_progress(80, 100)

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
    progress_recorder.set_progress(82, 100)
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
    progress_recorder.set_progress(82, 100)

    version_number = 0
    new_deal = ESS_Idea(deal_key=latest_deal_key, alpha_ticker=ticker, price=price, pt_up=pt_up,
                        pt_down=pt_down, pt_wic=pt_wic,
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

    # Associate the Deal with each of its Peers
    # First delete existing Peers
    peer_progress = 83
    for i in range(len(peers_data)):
        progress_recorder.set_progress(peer_progress, 100)
        peer_progress += 1
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

        peer_ev_sales_bf2 = blended_forward_2[peers_data[i]['peer']]['BEST_CURRENT_EV_BEST_SALES'].pop() if \
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


def add_new_deal_with_lock(bull_thesis_model_files, our_thesis_model_files, bear_thesis_model_files, update_id,
                           ticker,
                           situation_overview, company_overview, bull_thesis,
                           our_thesis, bear_thesis, pt_up, pt_wic, pt_down, unaffected_date, expected_close,
                           m_value, o_value,
                           s_value, a_value, i_value,
                           c_value, m_overview, o_overview, s_overview, a_overview, i_overview, c_overview,
                           ticker_hedge_length,
                           ticker_hedge_mappings, cix_index, price_target_date, multiples, category, catalyst,
                           deal_type,
                           catalyst_tier, hedges, gics_sector, lead_analyst, status, pt_up_check,
                           pt_down_check, pt_wic_check,
                           adjust_based_off, premium_format, multiples_mappings, progress_recorder, peer_tickers,
                           peer_hedge_weights, remove_file_ids=None):

    # Update ID should not be false here
    print('This is for Update ID:::: ' + str(update_id))
    with transaction.atomic():
        latest_deal_object = ESS_Idea.objects.select_for_update().get(id=update_id)
        print('Updating Deal by Acquiring a Lock on the Database Row...')

        end_date = datetime.datetime.strptime(unaffected_date, '%Y-%m-%d')
        start_date = end_date - relativedelta(months=3)
        start_date = datetime.datetime.strftime(start_date, "%Y%m%d")
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
            if datetime.datetime.strptime(each_date, '%Y-%m-%d') >= datetime.datetime.strptime(unaffected_date,
                                                                                               '%Y-%m-%d'):
                break
            index_of_unaffected_date += 1

        # 2 counters for hedge index changes. Upto Unaffacted Date and one after that
        progress_recorder.set_progress(60, 100)
        print('Index of Unaffected Date is: ' + str(index_of_unaffected_date))

        for i in range(0, index_of_unaffected_date):
            changes = []
            while counter < len(ratios) and i < len(peers_data[counter]['historical_prices']):
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
        progress_recorder.set_progress(70, 100)
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

        progress_recorder.set_progress(75, 100)
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

        progress_recorder.set_progress(80, 100)

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
        progress_recorder.set_progress(82, 100)
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
        progress_recorder.set_progress(82, 100)
        print('Updating the current IDEA. Creating a new Version ..%%')
        # Save as a new version
        all_versions = ESS_Idea.objects.all().filter(deal_key=latest_deal_object.deal_key).aggregate(Max('version_number'))
        version_number = all_versions['version_number__max'] + 1
        #version_number = int(latest_deal_object.version_number) + 1
        latest_deal_key = latest_deal_object.deal_key
        print('Recording this Change in Upside/Downside Change records....')
        ESS_Idea_Upside_Downside_Change_Records(ess_idea_id_id=update_id, deal_key=latest_deal_key, pt_up=pt_up,
                                                pt_wic=pt_wic, pt_down=pt_down,
                                                date_updated=datetime.datetime.now().date()
                                                .strftime('%Y-%m-%d')).save()

        print('Printing Version number & Deal Key of current deal..' + str(version_number)
              + " ->" + str(latest_deal_key))

        new_deal = ESS_Idea(deal_key=latest_deal_key, alpha_ticker=ticker, price=price, pt_up=pt_up,
                            pt_down=pt_down,
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
                            version_number=version_number, pt_up_check=pt_up_check, pt_down_check=pt_down_check,
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
        
        delete_thesis_files(new_deal.deal_key, remove_file_ids)

        # Associate the Deal with each of its Peers
        # First delete existing Peers
        peer_progress = 83
        for i in range(len(peers_data)):
            progress_recorder.set_progress(peer_progress, 100)
            peer_progress += 1
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

            peer_ev_sales_bf2 = blended_forward_2[peers_data[i]['peer']]['BEST_CURRENT_EV_BEST_SALES'].pop() if \
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


def add_new_deal_alpha_only(bull_thesis_model_files, our_thesis_model_files, bear_thesis_model_files, update_id, ticker,
                            situation_overview, company_overview, bull_thesis,
                            our_thesis, bear_thesis, pt_up, pt_wic, pt_down, unaffected_date, expected_close, m_value,
                            o_value,
                            s_value, a_value, i_value,
                            c_value, m_overview, o_overview, s_overview, a_overview, i_overview, c_overview,
                            ticker_hedge_length,
                            ticker_hedge_mappings, cix_index, price_target_date, multiples, category, catalyst,
                            deal_type,
                            catalyst_tier, hedges, gics_sector, lead_analyst, status, pt_up_check, pt_down_check,
                            pt_wic_check,
                            adjust_based_off, premium_format, multiples_mappings, progress_recorder, remove_file_ids=None):
    """ When no Peers are specified """

    end_date = datetime.datetime.strptime(unaffected_date, '%Y-%m-%d')
    start_date = end_date - relativedelta(months=3)

    start_date = datetime.datetime.strftime(start_date, "%Y%m%d")

    from datetime import timedelta
    # Reset End Date to Get Prices till date
    end_date = datetime.datetime.today().strftime(
        "%Y%m%d")  # - timedelta(days=3)).strftime("%Y%m%d") #Just for testing daily Calc
    r = requests.get("http://192.168.0.15:8080/wic/api/v1.0/general_histdata",
                     params={'idtype': "tickers", "fields": "PX_LAST",
                             "tickers": ticker,
                             "override": "", "start_date": start_date, "end_date": end_date},
                     timeout=15)  # Set a 15 secs Timeout

    ticker_counter = 0
    for every_row in r.json()['results']:
        if ticker in every_row:
            alpha_prices = r.json()['results'][ticker_counter][ticker]['fields']['PX_LAST']
            dates_array = r.json()['results'][ticker_counter][ticker]['fields']['date']
        ticker_counter += 1

    alpha_chart = []
    progress_recorder.set_progress(20, 100)

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
    progress_recorder.set_progress(30, 100)

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

    progress_recorder.set_progress(40, 100)

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
    latest_deal_key = ESS_Idea.objects.latest('deal_key').deal_key + 1
    progress_recorder.set_progress(50, 100)
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

    delete_thesis_files(new_deal.deal_key, remove_file_ids)


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
        # Money in Pence for UK stock...Divide by 100
        fcf['PX'] = fcf['PX'] / 100
    fcf['FCF yield'] = fcf['FCF'] / fcf['PX']

    return fcf[['Date', 'FCF yield']]


def delete_thesis_files(deal_key, remove_file_ids):
    try:
        # Delete Bull Thesis files
        bull_thesis_to_be_removed = remove_file_ids.get('BULL')
        if bull_thesis_to_be_removed:
            bull_thesis_to_be_removed = list(map(int, bull_thesis_to_be_removed))
            ESS_Idea_BullFileUploads.objects.filter(deal_key=deal_key, id__in=bull_thesis_to_be_removed).delete()
            print('Deleted ESS Bull Thesis files', bull_thesis_to_be_removed)

        # Delete Our Thesis files
        our_thesis_to_be_removed = remove_file_ids.get('OUR')
        if our_thesis_to_be_removed:
            our_thesis_to_be_removed = list(map(int, our_thesis_to_be_removed))
            ESS_Idea_OurFileUploads.objects.filter(deal_key=deal_key, id__in=our_thesis_to_be_removed).delete()
            print('Deleted ESS Our Thesis files', our_thesis_to_be_removed)

        # Delete Bear Thesis files
        bear_thesis_to_be_removed = remove_file_ids.get('BEAR')
        if bear_thesis_to_be_removed:
            bear_thesis_to_be_removed = list(map(int, bear_thesis_to_be_removed))
            ESS_Idea_BearFileUploads.objects.filter(deal_key=deal_key, id__in=bear_thesis_to_be_removed).delete()
            print('Deleted ESS Bear Thesis files', bear_thesis_to_be_removed)
    except Exception as error:
        print('Error Deleting files. File IDs are: ', remove_file_ids, error)
