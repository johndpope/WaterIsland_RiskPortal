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
from portfolio_optimization.models import  EssPotentialLongShorts, EssUniverseImpliedProbability
from slack_utils import get_channel_name


@shared_task
def refresh_ess_long_shorts_and_implied_probability():
    """ Shared Task executes at 8.15am and Post to Slack with an updated universe Table """
    today = datetime.datetime.now().date()
    api_host = bbgclient.bbgclient.get_next_available_host()
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                           + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)

    con = engine.connect()
    try:
        EssUniverseImpliedProbability.objects.filter(Date=today).delete() # Delete todays records
        ess_ideas_df = pd.read_sql_query("SELECT  A.id, A.alpha_ticker, A.price, A.pt_up, A.pt_wic, A.pt_down,"
                                         " A.unaffected_date, A.expected_close, A.gross_percentage, A.ann_percentage, "
                                         "A.hedged_volatility, A.implied_probability, A.category, A.catalyst,"
                                         " A.deal_type, A.catalyst_tier, A.gics_sector, A.hedges, A.lead_analyst, "
                                         "IF(model_up=0, A.pt_up, model_up) as model_up, "
                                         "IF(model_down=0, A.pt_down, model_down) as model_down, "
                                         "IF(model_wic=0, A.pt_wic, model_wic) as model_wic FROM " +
                                         settings.CURRENT_DATABASE +
                                         ".risk_ess_idea AS A INNER JOIN "
                                         "(SELECT deal_key, MAX(version_number) AS max_version FROM  "
                                         + settings.CURRENT_DATABASE + ".risk_ess_idea GROUP BY deal_key) AS B "
                                                                       "ON A.deal_key = B.deal_key AND "
                                                                       "A.version_number = B.max_version LEFT JOIN "
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
        ess_ideas_df = ess_ideas_df[['alpha_ticker', 'price', 'pt_up', 'pt_wic', 'pt_down', 'unaffected_date',
                                     'expected_close', 'category', 'catalyst',
                                     'deal_type', 'catalyst_tier',
                                     'gics_sector', 'hedges', 'lead_analyst', 'model_up', 'model_down', 'model_wic']]

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

        ess_ideas_df['Implied Probability'] = 1e2 * (ess_ideas_df['price'] - ess_ideas_df['pt_down']) / (
                ess_ideas_df['pt_up'] - ess_ideas_df['pt_down'])
        ess_ideas_df['Return/Risk'] = abs(
            (ess_ideas_df['pt_up'] / ess_ideas_df['price'] - 1) / (ess_ideas_df['pt_down'] / ess_ideas_df['price'] - 1))
        ess_ideas_df['Gross IRR'] = (ess_ideas_df['pt_up'] / ess_ideas_df['price'] - 1) * 1e2

        ess_ideas_df['Days to Close'] = (ess_ideas_df['expected_close'] - today).dt.days
        ess_ideas_df['Ann IRR'] = (ess_ideas_df['Gross IRR'] / ess_ideas_df['Days to Close']) * 365

        def calculate_adj_ann_irr(row):
            if row['hedges'] == 'Yes':
                return row['Ann IRR'] - 15

            return row['Ann IRR']

        ess_ideas_df['Adj. Ann IRR'] = ess_ideas_df.apply(calculate_adj_ann_irr, axis=1)
        # Targets currently hard-coded (should be customizable)
        long_short_targets = [['Merger Arbitrage', 75, 8, 95, 3], ['Dutch Tender', 75, 8, 95, 3],
                              ['Stub Value', 70, 10, 95, 5],
                              ['Spec M&A', 50, 40, 75, 10], ['Spin-Off', 35, 10, 55, 5],
                              ['Transformational M&A', 35, 10, 55, 5],
                              ['Turnaround', 35, 10, 55, 5], ['Post Re-org Equity', 35, 10, 55, 5]]
        ls_targets_df = pd.DataFrame(columns=['deal_type', 'long_prob', 'long_irr', 'short_prob', 'short_irr'],
                                     data=long_short_targets)
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
        avg_imp_prob = x[['deal_type', 'implied_probability']].groupby('deal_type').agg('mean').reset_index()
        avg_imp_prob.loc[len(avg_imp_prob)] = ['Soft Universe Imp. Prob',
                                               x[x['catalyst'] == 'Soft']['implied_probability'].mean()]

        avg_imp_prob['Date'] = today
        # --------------- SECTION FOR Tracking Univese, TAQ, AED Long/Short Implied Probabilities ---------------------
        query = "SELECT DISTINCT flat_file_as_of as `Date`, TradeGroup, Fund, Ticker, "\
                "LongShort, SecType, DealUpside, DealDownside "\
                "FROM wic.daily_flat_file_db  "\
                "WHERE Flat_file_as_of = (SELECT MAX(flat_file_as_of) from wic.daily_flat_file_db) AND Fund  "\
                "IN ('AED', 'TAQ') and AlphaHedge = 'Alpha' AND  "\
                "LongShort IN ('Long', 'Short') AND SecType = 'EQ' "\
                "AND Sleeve = 'Equity Special Situations' and amount<>0"\


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
        imp_prob_tracker_df['implied_probability'] = 1e2*(imp_prob_tracker_df['Price'] - imp_prob_tracker_df['DealDownside'])/(imp_prob_tracker_df['DealUpside'] - imp_prob_tracker_df['DealDownside'])

        imp_prob_tracker_df.replace([np.inf, -np.inf], np.nan, inplace=True)  #Replace Inf values
        grouped_funds_imp_prob = imp_prob_tracker_df[['Date', 'Fund', 'LongShort', 'implied_probability']].\
            groupby(['Date', 'Fund', 'LongShort']).mean().reset_index()

        grouped_funds_imp_prob['deal_type'] = grouped_funds_imp_prob['Fund'] + " " + grouped_funds_imp_prob['LongShort']
        grouped_funds_imp_prob = grouped_funds_imp_prob[['Date', 'deal_type', 'implied_probability']]

        # --------------- POTENTIAL LONG SHORT LEVEL IMPLIED PROBABILITY TRACKING --------------------------------------

        ess_potential_ls_df = pd.read_sql_query("SELECT * FROM " + settings.CURRENT_DATABASE +
                                                ".portfolio_optimization_esspotentiallongshorts", con=con)

        ess_potential_ls_df = ess_potential_ls_df[['alpha_ticker', 'price', 'implied_probability',
                                                   'potential_long', 'potential_short']]

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
        universe_long_short_implied_probabilities_df = ess_potential_ls_df[['LongShort',
                                                                            'implied_probability']].\
            groupby('LongShort').mean().reset_index()

        universe_long_short_implied_probabilities_df['Date'] = today
        universe_long_short_implied_probabilities_df = universe_long_short_implied_probabilities_df.\
            rename(columns = {'LongShort': 'deal_type'})

        universe_long_short_implied_probabilities_df = universe_long_short_implied_probabilities_df[
            ['Date', 'deal_type', 'implied_probability']]

        final_implied_probability_df = pd.concat([avg_imp_prob, all_ess_universe_implied_probability,
                                                  universe_long_short_implied_probabilities_df,
                                                  grouped_funds_imp_prob])
        del final_implied_probability_df['Date']

        final_implied_probability_df['Date'] = today

        final_implied_probability_df.to_sql(index=False, name='portfolio_optimization_essuniverseimpliedprobability',
                                            schema=settings.CURRENT_DATABASE, con=con, if_exists='append')

        print('refresh_ess_long_shorts_and_implied_probability : Task Done')

        message = '~ _(Risk Automation)_ *Potential Long/Shorts & Implied Probabilities Refereshed*  ' \
                  'Link for Potential Long/Short candidates: ' \
                  '_192.168.0.16:8000/portfolio_optimization/ess_potential_long_shorts_'

        # Post this Update to Slack
        # Format avg_imp_prob
        final_implied_probability_df = final_implied_probability_df[['deal_type', 'implied_probability']]
        final_implied_probability_df['implied_probability'] = final_implied_probability_df['implied_probability'].apply(lambda ip:
                                                                                        str(np.round(ip, decimals=2))
                                                                                        + " %")
        final_implied_probability_df.columns = ['Deal Type', 'Implied Probability']
        slack_message('ESS_IDEA_DATABASE_ERRORS.slack',
                      {'message': message,
                       'table': tabulate(final_implied_probability_df, headers='keys', tablefmt='pssql',
                                         numalign='right', showindex=False)},
                      channel=get_channel_name('ess_idea_db_logs'))

    except Exception as e:
        print('Error in ESS Potential Long Short Tasks ... ' + str(e))
    finally:
        con.close()
        print('Connection Closed....')
