import os
import datetime
import time
import numpy as np
import pandas as pd
from tabulate import tabulate
import bbgclient

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
import django

django.setup()
from risk.models import ESS_Idea
from celery import shared_task
from sqlalchemy import create_engine
from django.conf import settings
from django_slack import slack_message
from django.db import connection
from portfolio_optimization.models import EssPotentialLongShorts, EssUniverseImpliedProbability, EssDealTypeParameters, \
    ArbOptimizationUniverse, HardFloatOptimization, HardOptimizationSummary
from slack_utils import get_channel_name
from portfolio_optimization.portfolio_optimization_utils import calculate_pl_sec_impact
from .utils import parse_fld


def clean_model_up(row):
    return row['pt_up'] if not row['model_up'] else row['model_up']


def clean_model_down(row):
    return row['pt_down'] if not row['model_down'] else row['model_down']


@shared_task
def refresh_ess_long_shorts_and_implied_probability():
    """ Shared Task executes at 8.15am and Post to Slack with an updated universe Table """
    today = datetime.datetime.now().date()
    api_host = bbgclient.bbgclient.get_next_available_host()
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                           + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)

    con = engine.connect()
    try:
        EssUniverseImpliedProbability.objects.filter(Date=today).delete()  # Delete todays records
        ess_ideas_df = pd.read_sql_query(
            "SELECT  A.id as ess_idea_id, A.alpha_ticker, A.price, A.pt_up, A.pt_wic, A.pt_down,"
            " A.unaffected_date, A.expected_close, A.gross_percentage, A.ann_percentage, "
            "A.hedged_volatility, A.implied_probability, A.category, A.catalyst,"
            " A.deal_type, A.catalyst_tier, A.gics_sector, A.hedges, A.lead_analyst, "
            "IF(model_up=0, A.pt_up, model_up) as model_up, "
            "IF(model_down=0, A.pt_down, model_down) as model_down, "
            "IF(model_wic=0, A.pt_wic, model_wic) as model_wic, A.is_archived FROM " +
            settings.CURRENT_DATABASE +
            ".risk_ess_idea AS A INNER JOIN "
            "(SELECT deal_key, MAX(version_number) AS max_version FROM  "
            + settings.CURRENT_DATABASE + ".risk_ess_idea GROUP BY deal_key) AS B "
                                          "ON A.deal_key = B.deal_key AND "
                                          "A.version_number = B.max_version AND "
                                          "A.is_archived=0 "
                                          "LEFT JOIN "
                                          "(SELECT DISTINCT X.deal_key,"
                                          "X.pt_up as model_up, "
                                          "X.pt_down AS model_down, X.pt_wic AS model_wic "
                                          "FROM "
            + settings.CURRENT_DATABASE + ".risk_ess_idea_upside_downside_change_records  "
                                          "AS X "
                                          "INNER JOIN "
                                          "(SELECT deal_key, MAX(date_updated) AS "
                                          "MaxDate FROM " + settings.CURRENT_DATABASE +
            ".risk_ess_idea_upside_downside_change_records GROUP BY deal_key) AS Y ON "
            "X.deal_key = Y.deal_key WHERE X.date_updated = Y.MaxDate) AS ADJ ON "
            "ADJ.deal_key = A.deal_key ", con=con)

        # Take only Relevant Columnns
        ess_ideas_df = ess_ideas_df[['ess_idea_id', 'alpha_ticker', 'price', 'pt_up', 'pt_wic', 'pt_down',
                                     'unaffected_date', 'expected_close', 'category', 'catalyst',
                                     'deal_type', 'catalyst_tier', 'gics_sector', 'hedges', 'lead_analyst', 'model_up',
                                     'model_down', 'model_wic']]

        ess_ideas_tickers = ess_ideas_df['alpha_ticker'].unique()

        ess_ideas_live_prices = pd.DataFrame.from_dict(bbgclient.bbgclient.get_secid2field(ess_ideas_tickers, 'tickers',
                                                                                           ['PX_LAST'],
                                                                                           req_type='refdata',
                                                                                           api_host=api_host),
                                                       orient='index').reset_index()
        ess_ideas_live_prices.columns = ['alpha_ticker', 'Price']
        ess_ideas_live_prices['Price'] = ess_ideas_live_prices['Price'].apply(lambda px: float(px[0]) if px[0] else 0)
        ess_ideas_df = pd.merge(ess_ideas_df, ess_ideas_live_prices, how='left', on='alpha_ticker')
        del ess_ideas_df['price']
        ess_ideas_df.rename(columns={'Price': 'price'}, inplace=True)

        ess_ideas_df['model_up'] = ess_ideas_df.apply(clean_model_up, axis=1)
        ess_ideas_df['model_down'] = ess_ideas_df.apply(clean_model_down, axis=1)
        ess_ideas_df['Implied Probability'] = 1e2 * (ess_ideas_df['price'] - ess_ideas_df['model_down']) / (
                ess_ideas_df['model_up'] - ess_ideas_df['model_down'])
        ess_ideas_df['Return/Risk'] = abs(
            (ess_ideas_df['model_up'] / ess_ideas_df['price'] - 1) / (ess_ideas_df['model_down'] / ess_ideas_df['price'] - 1))
        ess_ideas_df['Gross IRR'] = (ess_ideas_df['model_up'] / ess_ideas_df['price'] - 1) * 1e2

        ess_ideas_df['Days to Close'] = (ess_ideas_df['expected_close'] - today).dt.days
        ess_ideas_df['Ann IRR'] = (ess_ideas_df['Gross IRR'] / ess_ideas_df['Days to Close']) * 365

        def calculate_adj_ann_irr(row):
            if row['hedges'] == 'Yes':
                return row['Ann IRR'] - 15

            return row['Ann IRR']

        ess_ideas_df['Adj. Ann IRR'] = ess_ideas_df.apply(calculate_adj_ann_irr, axis=1)
        # Targets currently hard-coded (should be customizable)
        ls_targets_df = pd.DataFrame.from_records(EssDealTypeParameters.objects.all().values())
        ls_targets_df.rename(columns={'long_probability': 'long_prob', 'short_probability': 'short_prob'}, inplace=True)
        ls_targets_df.drop(columns=['id', 'long_max_risk', 'long_max_size', 'short_max_risk', 'short_max_size'],
                           inplace=True)
        ess_ideas_df = pd.merge(ess_ideas_df, ls_targets_df, how='left', on='deal_type')
        ess_ideas_df['Potential Long'] = ess_ideas_df.apply(
            lambda x: 'Y' if (
                    (x['Implied Probability'] < x['long_prob']) and (x['Adj. Ann IRR'] > x['long_irr'])) else '',
            axis=1)
        ess_ideas_df['Potential Short'] = ess_ideas_df.apply(lambda x: 'Y' if (
                (x['Implied Probability'] > x['short_prob']) and (x['Adj. Ann IRR'] < x['short_irr'])) else '', axis=1)

        ess_ideas_df['Date'] = today
        x = ess_ideas_df.rename(
            columns={'Implied Probability': 'implied_probability', 'Return/Risk': 'return_risk',
                     'Gross IRR': 'gross_irr',
                     'Days to Close': 'days_to_close', 'Ann IRR': 'ann_irr', 'Adj. Ann IRR': 'adj_ann_irr',
                     'Potential Long': 'potential_long', 'Potential Short': 'potential_short'})
        x.to_sql(con=con, if_exists='append', schema=settings.CURRENT_DATABASE,
                 name='portfolio_optimization_esspotentiallongshorts', index=False)
        time.sleep(2)
        x['count'] = x['implied_probability'].apply(lambda y: 1 if not pd.isna(y) else np.nan)
        avg_imp_prob = x[['deal_type', 'count', 'implied_probability']].groupby('deal_type').agg(
            {'implied_probability': 'mean',
             'count': 'sum'}).reset_index()
        x.drop(columns=['count'], inplace=True)
        avg_imp_prob.loc[len(avg_imp_prob)] = ['Soft Universe Imp. Prob',
                                               x[x['catalyst'] == 'Soft']['implied_probability'].mean(),
                                               len(x[x['catalyst'] == 'Soft'])]

        avg_imp_prob['Date'] = today
        # --------------- SECTION FOR Tracking Univese, TAQ, AED Long/Short Implied Probabilities ---------------------
        query = "SELECT DISTINCT flat_file_as_of as `Date`, TradeGroup, Fund, Ticker, " \
                "LongShort, SecType, DealUpside, DealDownside " \
                "FROM wic.daily_flat_file_db  " \
                "WHERE Flat_file_as_of = (SELECT MAX(flat_file_as_of) from wic.daily_flat_file_db) AND Fund  " \
                "IN ('AED', 'TAQ') and AlphaHedge = 'Alpha' AND  " \
                "LongShort IN ('Long', 'Short') AND SecType = 'EQ' " \
                "AND Sleeve = 'Equity Special Situations' and amount<>0"

        imp_prob_tracker_df = pd.read_sql_query(query, con=con)
        imp_prob_tracker_df['Ticker'] = imp_prob_tracker_df['Ticker'] + ' EQUITY'
        ess_tickers = imp_prob_tracker_df['Ticker'].unique()

        live_price_df = pd.DataFrame.from_dict(bbgclient.bbgclient.get_secid2field(ess_tickers, 'tickers',
                                                                                   ['CRNCY_ADJ_PX_LAST'],
                                                                                   req_type='refdata',
                                                                                   api_host=api_host),
                                               orient='index').reset_index()
        live_price_df.columns = ['Ticker', 'Price']
        live_price_df['Price'] = live_price_df['Price'].apply(lambda px: float(px[0]) if px[0] else 0)
        imp_prob_tracker_df = pd.merge(imp_prob_tracker_df, live_price_df, how='left', on='Ticker')
        imp_prob_tracker_df['implied_probability'] = 1e2 * (
                    imp_prob_tracker_df['Price'] - imp_prob_tracker_df['DealDownside']) / (
                                                                 imp_prob_tracker_df['DealUpside'] -
                                                                 imp_prob_tracker_df['DealDownside'])

        imp_prob_tracker_df.replace([np.inf, -np.inf], np.nan, inplace=True)  # Replace Inf values
        imp_prob_tracker_df['count'] = imp_prob_tracker_df['implied_probability'].apply(
            lambda x: 1 if not pd.isna(x) else np.nan)
        grouped_funds_imp_prob = imp_prob_tracker_df[['Date', 'Fund', 'LongShort', 'implied_probability', 'count']]. \
            groupby(['Date', 'Fund', 'LongShort']).agg({'implied_probability': 'mean', 'count': 'sum'}).reset_index()
        imp_prob_tracker_df.drop(columns=['count'], inplace=True)

        grouped_funds_imp_prob['deal_type'] = grouped_funds_imp_prob['Fund'] + " " + grouped_funds_imp_prob['LongShort']
        grouped_funds_imp_prob = grouped_funds_imp_prob[['Date', 'deal_type', 'implied_probability', 'count']]

        # --------------- POTENTIAL LONG SHORT LEVEL IMPLIED PROBABILITY TRACKING --------------------------------------
        ess_potential_ls_df = pd.read_sql_query("SELECT * FROM " + settings.CURRENT_DATABASE +
                                                ".portfolio_optimization_esspotentiallongshorts where Date='" +
                                                today.strftime("%Y-%m-%d") + "'", con=con)

        catalyst_rating_dfs = ess_potential_ls_df[['alpha_ticker', 'catalyst', 'catalyst_tier', 'price',
                                                   'implied_probability', 'potential_long', 'potential_short']]

        ess_potential_ls_df = ess_potential_ls_df[['alpha_ticker', 'price', 'implied_probability',
                                                   'potential_long', 'potential_short']]

        # -------------- Section for Implied Probabilities Grouped by Catalyst and Tiers -------------------------------
        catalyst_rating_dfs['deal_type'] = catalyst_rating_dfs.apply(lambda x: x['catalyst'] + "-" +
                                                                               x['catalyst_tier'], axis=1)

        catalyst_rating_dfs['count'] = catalyst_rating_dfs['implied_probability'].apply(lambda y: 1 if not pd.isna(y) else np.nan)

        catalyst_implied_prob = catalyst_rating_dfs[['deal_type', 'implied_probability', 'count']].groupby('deal_type').agg({'implied_probability': 'mean','count': 'sum'}).reset_index()
        catalyst_implied_prob['Date'] = today

        def classify_ess_longshorts(row):
            classification = 'Universe (Unclassified)'
            if row['potential_long'] == 'Y':
                classification = 'Universe (Long)'
            if row['potential_short'] == 'Y':
                classification = 'Universe (Short)'

            return classification

        # Get the Whole ESS Universe Implied Probability

        universe_data = ['ESS IDEA Universe', ess_potential_ls_df['implied_probability'].mean(),
                         len(ess_potential_ls_df)]
        all_ess_universe_implied_probability = pd.DataFrame(columns=['deal_type', 'implied_probability', 'count'],
                                                            data=[universe_data])

        all_ess_universe_implied_probability['Date'] = today

        # Section for only Long Short Tagging...

        ess_potential_ls_df['LongShort'] = ess_potential_ls_df.apply(classify_ess_longshorts, axis=1)
        ess_potential_ls_df['count'] = ess_potential_ls_df['implied_probability'].apply(
            lambda x: 1 if not pd.isna(x) else np.nan)
        universe_long_short_implied_probabilities_df = ess_potential_ls_df[['LongShort', 'count',
                                                                            'implied_probability']].groupby(
            ['LongShort']).agg({'implied_probability': 'mean', 'count': 'sum'}).reset_index()

        universe_long_short_implied_probabilities_df['Date'] = today
        universe_long_short_implied_probabilities_df = universe_long_short_implied_probabilities_df. \
            rename(columns={'LongShort': 'deal_type'})

        universe_long_short_implied_probabilities_df = universe_long_short_implied_probabilities_df[
            ['Date', 'deal_type', 'implied_probability', 'count']]

        final_implied_probability_df = pd.concat([avg_imp_prob, all_ess_universe_implied_probability,
                                                  universe_long_short_implied_probabilities_df,
                                                  grouped_funds_imp_prob, catalyst_implied_prob])
        del final_implied_probability_df['Date']

        final_implied_probability_df['Date'] = today
        final_implied_probability_df.replace([np.inf, -np.inf], np.nan, inplace=True)  # Replace Inf values
        final_implied_probability_df.to_sql(index=False, name='portfolio_optimization_essuniverseimpliedprobability',
                                            schema=settings.CURRENT_DATABASE, con=con, if_exists='append')

        print('refresh_ess_long_shorts_and_implied_probability : Task Done')

        message = '~ _(Risk Automation)_ *Potential Long/Shorts & Implied Probabilities Refereshed*  ' \
                  'Link for Potential Long/Short candidates: ' \
                  'http://192.168.0.16:8000/portfolio_optimization/ess_potential_long_shorts'

        # Post this Update to Slack
        # Format avg_imp_prob
        final_implied_probability_df = final_implied_probability_df[['deal_type', 'implied_probability', 'count']]
        final_implied_probability_df['implied_probability'] = final_implied_probability_df['implied_probability'].apply(
            lambda ip: str(np.round(ip, decimals=2)) + " %")
        final_implied_probability_df.columns = ['Deal Type', 'Implied Probability', 'Count']

        slack_message('ESS_IDEA_DATABASE_ERRORS.slack',
                      {'message': message,
                       'table': tabulate(final_implied_probability_df, headers='keys', tablefmt='pssql',
                                         numalign='right', showindex=False)},
                      channel=get_channel_name('ess_idea_db_logs'))

    except Exception as e:
        print('Error in ESS Potential Long Short Tasks ... ' + str(e))
        slack_message('ESS_IDEA_DATABASE_ERRORS.slack', {'message': str(e)},
                      channel=get_channel_name('ess_idea_db_logs'))
    finally:
        con.close()


@shared_task
def get_arb_optimization_ranks():    # Task runs every morning at 7pm and Posts to Slack
    """ For the ARB Optimized Sleeve & Other M&A Sleeve, calculate the Gross RoR, Ann. RoR
    1. Gross RoR : (AllInSpread/PX_LAST) * 100
    2. Ann. RoR: (Gross RoR/Days to Close) * 365
    3. Risk (%): (NAV Impact)/(% of ARB AUM)     : % of Sleeve Current in positions database
    4. Expected Volatility: (Sqrt(days_to_close) * Sqrt(Gross RoR) * Sqrt(ABS(Risk(%))) / 10
    """
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                               + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)

    con = engine.connect()
    today = datetime.datetime.now().date()
    try:
        query = "SELECT DISTINCT tradegroup,ticker,SecType,AlphaHedge,DealValue as deal_value, Sleeve as sleeve, " \
                "Bucket as bucket, CatalystTypeWIC as catalyst, " \
                "CatalystRating as catalyst_rating,CurrentMktVal,Strike as StrikePrice, PutCall, " \
                "FXCurrentLocalToBase as FxFactor, " \
                "amount*factor as QTY, ClosingDate as closing_date, Target_Ticker as target_ticker, LongShort as long_short,"\
                "TargetLastPrice/FXCurrentLocalToBase as target_last_price,Price as SecurityPrice, AllInSpread as all_in_spread, " \
                "DealDownside as deal_downside, datediff(ClosingDate, curdate()) as days_to_close, "\
                "PctOfSleeveCurrent, aum from wic.daily_flat_file_db where " \
                "Flat_file_as_of = (Select max(Flat_file_as_of) "\
                "from wic.daily_flat_file_db) and LongShort in ('Long', 'Short') "\
                "and amount<>0 and SecType in ('EQ', 'EXCHOPT') and Fund = 'ARB'"

        # Create two Dataframes (One for adjusting RoRs with Hedges and another @ Tradegroup level for merging later...)
        df = pd.read_sql_query(query, con=con)
        tradegroup_level_df = df.copy()
        del tradegroup_level_df['ticker']
        del tradegroup_level_df['target_ticker']
        del tradegroup_level_df['SecType']
        del tradegroup_level_df['AlphaHedge']
        del tradegroup_level_df['CurrentMktVal']
        del tradegroup_level_df['PutCall']
        del tradegroup_level_df['StrikePrice']
        del tradegroup_level_df['QTY']
        del tradegroup_level_df['FxFactor']
        del tradegroup_level_df['SecurityPrice']
        del tradegroup_level_df['PctOfSleeveCurrent']
        # Drop the duplicates
        tradegroup_level_df = tradegroup_level_df.drop_duplicates(keep='first')
        nav_impacts_df = pd.read_sql_query('SELECT TradeGroup as tradegroup, BASE_CASE_NAV_IMPACT_ARB FROM ' +
                                           settings.CURRENT_DATABASE + '.risk_reporting_dailynavimpacts', con=con)

        df['PnL'] = df.apply(calculate_pl_sec_impact, axis=1)
        # Delete the Security Price column
        del df['SecurityPrice']

        df['pnl_impact'] = 1e2*(df['PnL']/df['aum'])

        rors_df = df[['tradegroup', 'ticker', 'pnl_impact']].groupby(['tradegroup'])['pnl_impact'].sum().reset_index()

        def get_pct_of_sleeve_alpha(row):
            sleeve_pct_df = df[df['tradegroup'] == row]
            try:
                alpha_pct = sleeve_pct_df[sleeve_pct_df['AlphaHedge'] == 'Alpha']['PctOfSleeveCurrent'].iloc[0]
            except IndexError:
                alpha_pct = 0
            # Returns the Alpha Current Sleeve %
            return float(alpha_pct)

        rors_df['pct_of_sleeve_current'] = rors_df['tradegroup'].apply(get_pct_of_sleeve_alpha)

        # Calculate the RoR
        rors_df['gross_ror'] = 1e2*(rors_df['pnl_impact']/rors_df['pct_of_sleeve_current'])
        rors_df = pd.merge(rors_df, tradegroup_level_df, how='left', on=['tradegroup'])  # Adds Tradegroup level cols.

        rors_df['ann_ror'] = (rors_df['gross_ror']/rors_df['days_to_close'])*365
        rors_df = pd.merge(rors_df, nav_impacts_df, how='left', on='tradegroup')
        rors_df.rename(columns={'BASE_CASE_NAV_IMPACT_ARB': 'base_case_nav_impact'}, inplace=True)

        rors_df['base_case_nav_impact'] = rors_df['base_case_nav_impact'].astype(float)
        rors_df['pct_of_sleeve_current'] = rors_df['pct_of_sleeve_current'].astype(float)
        rors_df['risk_pct'] = 1e2 * (rors_df['base_case_nav_impact']/rors_df['pct_of_sleeve_current'])
        rors_df['expected_vol'] = (np.sqrt(rors_df['days_to_close']) * np.sqrt(rors_df['gross_ror']) *
                                   np.sqrt(abs(rors_df['risk_pct'])))/10

        rors_df['date_updated'] = today

        rors_df.replace([np.inf, -np.inf], np.nan, inplace=True)
        # Remove unwanted columns
        del rors_df['aum']

        rors_df[['gross_ror', 'ann_ror', 'base_case_nav_impact', 'risk_pct', 'expected_vol']] = \
            rors_df[['gross_ror', 'ann_ror', 'base_case_nav_impact', 'risk_pct', 'expected_vol']].fillna(value=0)

        ArbOptimizationUniverse.objects.filter(date_updated=today).delete()
        rors_df.to_sql(name='portfolio_optimization_arboptimizationuniverse', schema=settings.CURRENT_DATABASE,
                       if_exists='append', index=False, con=con)
        con.close()
        slack_message('eze_uploads.slack', {'null_risk_limits':
                                            str("_(Risk Automation)_ Successfully calculated ARB RoRs. "
                                                "Visit http://192.168.0.16:8000/portfolio_optimization/merger_arb_rors")},
                      channel=get_channel_name('portal_downsides'), token=settings.SLACK_TOKEN)

    except Exception as e:
        print(e)
    finally:
        print('Closing connection to Relational Database Service...')
        con.close()

    return 'Arb RoRs calculated!'


@shared_task
def arb_hard_float_optimization():
    """ Purpose of this task is to take Hard M&A Deals in ARB and list scenarios to show Firm % of Float if Mstarts
        get to 1x AUM of ARB and 2x AUM of ARB Fund. Run this task after ARB Rate of Returns task... """

    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                               + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
    con = engine.connect()
    try:
        api_host = bbgclient.bbgclient.get_next_available_host()
        max_date = "(SELECT MAX(date_updated) from "+settings.CURRENT_DATABASE+".portfolio_optimization_arboptimizationuniverse)"  # RoRs
        comments_df_query = "SELECT tradegroup, notes, rebal_multiples, rebal_target FROM "+settings.CURRENT_DATABASE + \
                            ".portfolio_optimization_hardfloatoptimization WHERE date_updated = " \
                            "(SELECT MAX(date_updated) FROM " + settings.CURRENT_DATABASE + \
                            ".portfolio_optimization_hardfloatoptimization)"

        comments_df = pd.read_sql_query(comments_df_query, con=con)   # Comments & Rebal Mult,Target
        arb_df = pd.read_sql_query("SELECT * FROM "+settings.CURRENT_DATABASE+".portfolio_optimization_arboptimizationuniverse WHERE "
                                   "date_updated="+max_date, con=con)

        cols_to_work_on = ['tradegroup', 'sleeve', 'catalyst', 'catalyst_rating', 'closing_date', 'target_last_price',
                           'deal_value', 'all_in_spread', 'days_to_close', 'gross_ror', 'ann_ror', 'risk_pct',
                           'expected_vol']

        arb_df = arb_df[cols_to_work_on]
        shares_query = "SELECT TradeGroup,Target_Ticker,TargetLastPrice/FXCurrentLocalToBase as TargetLastPrice, Fund, " \
                       "SUM(amount*factor) AS TotalQty, aum, " \
                       "100*(amount*factor*(TargetLastPrice/FXCurrentLocalToBase))/aum " \
                       "AS Current_Pct_ofAUM FROM wic.daily_flat_file_db WHERE " \
                       "Flat_file_as_of = (SELECT MAX(flat_file_as_of) FROM wic.daily_flat_file_db) AND " \
                       "CatalystTypeWIC = 'HARD' AND amount<>0 AND SecType IN ('EQ') AND AlphaHedge ='Alpha' AND " \
                       "LongShort='Long' AND TradeGroup IS NOT NULL AND Fund IN " \
                       "('ARB', 'MACO', 'MALT', 'CAM', 'LG', 'LEV', 'AED')  GROUP BY TradeGroup, Fund, aum;"

        current_shares_df = pd.read_sql_query(shares_query, con=con)

        current_shares_df['Target_Ticker'] = current_shares_df['Target_Ticker'].apply(lambda x: x+" EQUITY")

        arb_shares_df = current_shares_df[current_shares_df['Fund'] == 'ARB']  # Slice shares for ARB
        arb_shares_df.rename(columns={'Current_Pct_ofAUM':'ARB_Pct_of_AUM'}, inplace=True)

        # Slice AED and LG separately
        aed_shares_df = current_shares_df[current_shares_df['Fund'] == 'AED']
        lg_shares_df = current_shares_df[current_shares_df['Fund'] == 'LG']
        aed_aum = aed_shares_df['aum'].unique()[0]
        lg_aum = lg_shares_df['aum'].unique()[0]

        # Following Inline function returns Multistrat Ration w.r.t ARB
        def get_mstrat_quantity(row, fund):
            if fund == 'AED':
                aum = aed_aum
            else:
                aum = lg_aum
            quantity = (0.01*row['ARB_Pct_of_AUM']*aum)/row['TargetLastPrice']
            return quantity

        # Get the Quantity if MStarts asuume 1x AUM of ARB (in their respective Funds)
        arb_shares_df['AED Qty 1x'] = arb_shares_df.apply(lambda x: get_mstrat_quantity(x, 'AED'), axis=1)
        arb_shares_df['LG Qty 1x'] = arb_shares_df.apply(lambda x: get_mstrat_quantity(x, 'LG'), axis=1)

        # Get 2x quantitity of Mstrats go to 2x
        arb_shares_df['AED Qty 2x'] = arb_shares_df['AED Qty 1x'].apply(lambda x: x*2)
        arb_shares_df['LG Qty 2x'] = arb_shares_df['LG Qty 1x'].apply(lambda x: x*2)

        # Get Current Firmwide Quantity of Shares excluding Mstrats (LG and AED)
        current_qty = current_shares_df[~(current_shares_df['Fund'].isin(['AED', 'LG']))][['TradeGroup', 'TotalQty']]

        # Add 1x and 2x Quantity Columns
        aed_1x_shares = arb_shares_df[['TradeGroup', 'AED Qty 1x']]
        lg_1x_shares = arb_shares_df[['TradeGroup', 'LG Qty 1x']]
        aed_2x_shares = arb_shares_df[['TradeGroup', 'AED Qty 2x']]
        lg_2x_shares = arb_shares_df[['TradeGroup', 'LG Qty 2x']]

        # Rename
        aed_1x_shares.columns = ['TradeGroup', 'TotalQty']
        lg_1x_shares.columns = ['TradeGroup', 'TotalQty']
        aed_2x_shares.columns = ['TradeGroup', 'TotalQty']
        lg_2x_shares.columns = ['TradeGroup', 'TotalQty']

        shares_1x = pd.concat([current_qty, aed_1x_shares, lg_1x_shares])
        shares_2x = pd.concat([current_qty, aed_2x_shares, lg_2x_shares])

        # Get Firmwide Shares if Mstart go to 1x and 2x
        firmwide_shares_1x = shares_1x.groupby('TradeGroup').sum().reset_index()
        firmwide_shares_2x = shares_2x.groupby('TradeGroup').sum().reset_index()

        firmwide_shares_1x.columns = ['TradeGroup', 'TotalQty_1x']
        firmwide_shares_2x.columns = ['TradeGroup', 'TotalQty_2x']
        firmwide_current_shares = current_shares_df[['TradeGroup', 'Target_Ticker', 'TotalQty']].\
            groupby(['TradeGroup', 'Target_Ticker']).sum().reset_index()

        all_shares = pd.merge(firmwide_current_shares, firmwide_shares_1x, on='TradeGroup')
        all_shares = pd.merge(all_shares, firmwide_shares_2x, on='TradeGroup')

        unique_target_tickers = list(all_shares['Target_Ticker'].unique())

        # Get the Current Float for all tickers
        current_floats = bbgclient.bbgclient.get_secid2field(unique_target_tickers,'tickers',
                                                              ['EQY_FLOAT'], req_type='refdata', api_host=api_host)

        all_shares['FLOAT'] = all_shares['Target_Ticker'].apply(lambda x:
                                                                parse_fld(current_floats,'EQY_FLOAT', x)
                                                                if not pd.isnull(x) else None)
        all_shares['FLOAT'] = all_shares['FLOAT'] * 1000000

        # Calculates the Current % of Float for current portfolio, 1x Mstart and 2x Mstrat
        all_shares['Current % of Float'] = 1e2*(all_shares['TotalQty']/all_shares['FLOAT'])

        all_shares['Firm % of Float if Mstart 1x'] = 1e2*(all_shares['TotalQty_1x']/all_shares['FLOAT'])
        all_shares['Firm % of Float if Mstart 2x'] = 1e2*(all_shares['TotalQty_2x']/all_shares['FLOAT'])

        lg_current_shares = current_shares_df[current_shares_df['Fund'].isin(['LG'])]
        aed_current_shares = current_shares_df[current_shares_df['Fund'].isin(['AED'])]
        arb_current_shares = current_shares_df[current_shares_df['Fund'].isin(['ARB'])]

        # Below function to get the AUM Multiplier i.e times of ARBs AUM we currenly in AED and LG

        def get_aum_multiplier(row, fund):
            aum_multiplier = 0
            df_arb = arb_current_shares[arb_current_shares['TradeGroup'] == row['TradeGroup']]
            if len(df_arb) == 0:
                return np.NAN

            if fund == 'LG':
                df_ = lg_current_shares[lg_current_shares['TradeGroup'] == row['TradeGroup']]
                if len(df_) > 0:
                    aum_multiplier = df_['Current_Pct_ofAUM'].iloc[0]/df_arb['Current_Pct_ofAUM'].iloc[0]
            else:
                df_ = aed_current_shares[aed_current_shares['TradeGroup'] == row['TradeGroup']]
                if len(df_) > 0:
                    aum_multiplier = df_['Current_Pct_ofAUM'].iloc[0]/df_arb['Current_Pct_ofAUM'].iloc[0]

            return aum_multiplier

        all_shares['AED AUM Mult'] = all_shares.apply(lambda x: get_aum_multiplier(x, 'AED'), axis=1)
        all_shares['LG AUM Mult'] = all_shares.apply(lambda x: get_aum_multiplier(x, 'LG'), axis=1)

        # Get % of AUMs
        def get_aed_pct_of_aum(row, fund):
            if fund == 'ARB':
                aum_df_ = arb_current_shares
            else:
                aum_df_ = aed_shares_df

            return_value = 0
            aum_ = aum_df_[aum_df_['TradeGroup'] == row['TradeGroup']]
            if len(aum_) > 0:
                return aum_['Current_Pct_ofAUM'].iloc[0]
            return return_value

        all_shares['aed_pct_of_aum'] = all_shares.apply(lambda x: get_aed_pct_of_aum(x, 'AED'), axis=1)
        all_shares['arb_pct_of_aum'] = all_shares.apply(lambda x: get_aed_pct_of_aum(x, 'ARB'), axis=1)

        all_shares.columns = ['tradegroup', 'target_ticker', 'total_qty', 'total_qty_1x', 'total_qty_2x', 'eqy_float',
                              'current_pct_of_float', 'firm_pct_float_mstrat_1x', 'firm_pct_float_mstrat_2x',
                              'aed_aum_mult', 'lg_aum_mult', 'aed_pct_of_aum', 'arb_pct_of_aum']

        # Merge ARB_DF (Rate of Returns with Float DF)
        final_hard_opt_df = pd.merge(arb_df, all_shares, how='left', on='tradegroup')

        final_hard_opt_df['date_updated'] = datetime.datetime.now().date()

        # Delete unwanted columns
        final_hard_opt_df = pd.merge(final_hard_opt_df, comments_df,how='left', on='tradegroup')

        # Get the NAV Impacts for Risk Multiples
        nav_impacts_query = "SELECT tradegroup, OUTLIER_NAV_IMPACT_ARB AS arb_outlier_risk, OUTLIER_NAV_IMPACT_AED AS " \
                            "aed_outlier_risk, OUTLIER_NAV_IMPACT_LG AS lg_outlier_risk FROM "\
                            + settings.CURRENT_DATABASE + ".risk_reporting_dailynavimpacts"

        nav_impacts_df = pd.read_sql_query(nav_impacts_query, con=con)
        numeric_cols = ['arb_outlier_risk', 'aed_outlier_risk', 'lg_outlier_risk']
        nav_impacts_df[numeric_cols] = nav_impacts_df[numeric_cols].apply(pd.to_numeric)
        final_hard_opt_df = pd.merge(final_hard_opt_df, nav_impacts_df, on='tradegroup', how='left')

        final_hard_opt_df['aed_risk_mult'] = final_hard_opt_df['aed_outlier_risk'] / final_hard_opt_df['arb_outlier_risk']
        final_hard_opt_df['lg_risk_mult'] = final_hard_opt_df['lg_outlier_risk'] / final_hard_opt_df['arb_outlier_risk']

        HardFloatOptimization.objects.filter(date_updated=datetime.datetime.now().date()).delete()

        # Adjust for the Rebal Targets
        final_hard_opt_df['rebal_target'] = final_hard_opt_df.apply(lambda x:
                                                                    np.round((x['rebal_multiples'] * x['arb_pct_of_aum']
                                                                              ), decimals=2) if not
                                                                    pd.isna(x['rebal_multiples'])
                                                                    else x['aed_pct_of_aum'], axis=1)

        # Section for Time Weighted Rate of Return Calculation...
        def exclude_from_ror(row):
            if ((row['days_to_close'] < 22) and (row['all_in_spread'] < 0.1)) or (row['days_to_close'] < 6):
                return True
            return False

        final_hard_opt_df['is_excluded'] = final_hard_opt_df.apply(exclude_from_ror, axis=1)
        final_hard_opt_df_excluded = final_hard_opt_df[final_hard_opt_df['is_excluded'] == True]
        final_hard_opt_df = final_hard_opt_df[final_hard_opt_df['is_excluded'] == False]

        final_hard_opt_df['weighted_gross_nav_potential'] = (final_hard_opt_df['gross_ror'] * final_hard_opt_df['aed_aum_mult'])/100
        # Calculate the Cumulative Sum
        final_hard_opt_df['weighted_nav_cumsum'] = final_hard_opt_df['weighted_gross_nav_potential'].cumsum()
        # Get the Mstrat % of AUM
        final_hard_opt_df['non_excluded_pct_aum_cumsum'] = final_hard_opt_df['rebal_target'].cumsum()

        # Get the Current Rtn Weight Duration
        final_hard_opt_df["curr_rtn_wt_duration"] = final_hard_opt_df['days_to_close'].\
            mul(final_hard_opt_df['weighted_gross_nav_potential']).cumsum().\
            div(final_hard_opt_df['weighted_gross_nav_potential'].cumsum())

        # Get the RWD, ROR
        final_hard_opt_df['curr_rwd_ror'] = final_hard_opt_df['weighted_nav_cumsum']/final_hard_opt_df['non_excluded_pct_aum_cumsum']/\
                                    final_hard_opt_df['curr_rtn_wt_duration']*360
        final_hard_opt_df['curr_rwd_ror'] = 1e2 * final_hard_opt_df['curr_rwd_ror']

        #  Merge back Excluded deals after adding new columns
        final_hard_opt_df_excluded['weighted_nav_cumsum'] = None
        final_hard_opt_df_excluded['non_excluded_pct_aum_cumsum'] = None
        final_hard_opt_df_excluded['curr_rtn_wt_duration'] = None
        final_hard_opt_df_excluded['curr_rwd_ror'] = None

        final_hard_opt_df = pd.concat([final_hard_opt_df, final_hard_opt_df_excluded])

        # Replace Infinity values
        final_hard_opt_df.replace([np.inf, -np.inf], np.nan, inplace=True)  # Replace Inf values

        final_hard_opt_df.to_sql(name='portfolio_optimization_hardfloatoptimization', schema=settings.CURRENT_DATABASE,
                                 if_exists='append', index=False, con=con)

        hard_optimized_summary()
        slack_message('eze_uploads.slack', {'null_risk_limits':
                                            str("_(Risk Automation)_ ARB Hard Catalyst Optimization Completed... "
                                                "Visit http://192.168.0.16:8000/portfolio_optimization/arb_hard_optimization"
                                                )},
                      channel=get_channel_name('portal_downsides'), token=settings.SLACK_TOKEN)

    except Exception as e:
        print(e)
        slack_message('eze_uploads.slack', {'null_risk_limits':
                                            str("_(Risk Automation)_ *ERROR in HardOpt!*... ") + str(e)
                                            },
                      channel=get_channel_name('portal_downsides'), token=settings.SLACK_TOKEN)

    finally:
        print('Closing Connection to Relational Database Service...')
        con.close()


@shared_task
def hard_optimized_summary():
    """ Task runs after the above task is completed. Creates a Summary of the Hard-Optimized schedule """
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                               + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
    con = engine.connect()
    try:
        #  Get current data
        current_invested_query = "SELECT TradeGroup, Fund, CurrentMktVal_Pct FROM wic.daily_flat_file_db "\
                                 "WHERE Flat_file_as_of = (SELECT MAX(flat_file_as_of) FROM wic.daily_flat_file_db) "\
                                 "AND Fund IN ('ARB', 'AED') AND LongShort = 'Long' AND amount<>0 AND " \
                                 "Ticker NOT LIKE '%%CASH%%' AND AlphaHedge LIKE 'Alpha' and Sleeve='Merger Arbitrage'"
        current_invested = pd.read_sql_query(current_invested_query, con=con)
        arb_no_of_deals = current_invested[current_invested['Fund'] == 'ARB']['TradeGroup'].nunique()
        arb_pct_invested = current_invested[current_invested['Fund'] == 'ARB']['CurrentMktVal_Pct'].sum()

        aed_no_of_deals = current_invested[current_invested['Fund'] == 'AED']['TradeGroup'].nunique()
        aed_pct_invested = current_invested[current_invested['Fund'] == 'AED']['CurrentMktVal_Pct'].sum()

        # Summary based on Hard Optimization and Rebalanced Targets
        rebal_query = "SELECT * FROM "+ settings.CURRENT_DATABASE+".portfolio_optimization_hardfloatoptimization " \
                      "WHERE date_updated = (SELECT MAX(date_updated) FROM " + settings.CURRENT_DATABASE + \
                      ".portfolio_optimization_hardfloatoptimization)"

        rebal_query_df = pd.read_sql_query(rebal_query, con=con)
        # Remove Excluded ones
        rebal_query_df = rebal_query_df[rebal_query_df['is_excluded'] == False]
        # Get Hard-1 Optimized RoRs
        hard_one_df = rebal_query_df[((rebal_query_df['catalyst'] == 'HARD') & (rebal_query_df['catalyst_rating'] == '1'))]
        average_optimized_rors = hard_one_df['ann_ror'].mean()

        weighted_arb_ror = (hard_one_df['ann_ror']*hard_one_df['arb_pct_of_aum']).sum() * 0.01
        weighted_aed_ror = rebal_query_df['curr_rwd_ror'].min()

        # Following metrics based on the Adjustable column
        hard_aed = rebal_query_df[rebal_query_df['catalyst'] == 'HARD']
        hard_aed_pct_invested = hard_aed['rebal_target'].sum()

        # Get the whole AED Fund % invested based on the Rebalanced Targets
        aed_df = current_invested[~current_invested['TradeGroup'].isin(rebal_query_df['tradegroup'].unique())]

        rebalanced_aed_pct_invested = rebal_query_df[['tradegroup', 'rebal_target']]
        rebalanced_aed_pct_invested['Fund'] = 'AED'
        rebalanced_aed_pct_invested.rename(columns={'rebal_target': 'CurrentMktVal_Pct', 'tradegroup': 'TradeGroup'},
                                           inplace=True)

        # Concatenate the 2 dataframes
        aed_rebalanced_df = pd.concat([rebalanced_aed_pct_invested, aed_df])

        aed_fund_pct_invested_rebalanced = aed_rebalanced_df['CurrentMktVal_Pct'].sum()
        now = datetime.datetime.now().date()
        HardOptimizationSummary.objects.filter(date_updated=now).delete()

        HardOptimizationSummary(date_updated=now, average_optimized_rors=average_optimized_rors,
                                weighted_arb_rors=weighted_arb_ror, weighted_aed_ror=weighted_aed_ror,
                                arb_number_of_deals=arb_no_of_deals, arb_pct_invested=arb_pct_invested,
                                aed_number_of_deals=aed_no_of_deals, aed_currently_invested=aed_pct_invested,
                                aed_hard_pct_invested=hard_aed_pct_invested, aed_fund_pct_invested=aed_fund_pct_invested_rebalanced).save()

    except Exception as e:
        print(e)
        slack_message('eze_uploads.slack', {'null_risk_limits':
                                            str("_(Risk Automation)_ *ERROR in HardOpt (Summary)!*... ") + str(e)
                                            },
                      channel=get_channel_name('portal_downsides'), token=settings.SLACK_TOKEN)
    finally:
        con.close()
        print('Closing connection to Relational Database Service')
