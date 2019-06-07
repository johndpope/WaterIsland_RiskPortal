import os
import datetime
import numpy as np
import pandas as pd
from tabulate import tabulate
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
import django
django.setup()
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

    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                           + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)

    con = engine.connect()
    try:
        EssPotentialLongShorts.objects.all().delete()
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

        x = ess_ideas_df.rename(
            columns={'Implied Probability': 'implied_probability', 'Return/Risk': 'return_risk',
                     'Gross IRR': 'gross_irr',
                     'Days to Close': 'days_to_close', 'Ann IRR': 'ann_irr', 'Adj. Ann IRR': 'adj_ann_irr',
                     'Potential Long': 'potential_long', 'Potential Short': 'potential_short'})
        x.to_sql(con=con, if_exists='append', schema=settings.CURRENT_DATABASE,
                 name='portfolio_optimization_esspotentiallongshorts', index=False)

        avg_imp_prob = x[['deal_type', 'implied_probability']].groupby('deal_type').agg('mean').reset_index()
        avg_imp_prob.loc[len(avg_imp_prob)] = ['Soft Universe Imp. Prob',
                                               x[x['catalyst'] == 'Soft']['implied_probability'].mean()]

        avg_imp_prob['Date'] = today
        avg_imp_prob.to_sql(index=False, name='portfolio_optimization_essuniverseimpliedprobability',
                            schema=settings.CURRENT_DATABASE, con=con, if_exists='append')

        print('refresh_ess_long_shorts_and_implied_probability : Task Done')

        message = '~ _(Risk Automation)_ *Potential Long/Shorts & Implied Probabilities Refereshed*  ' \
                  'Link for Potential Long/Short candidates: ' \
                  '_192.168.0.16:8000/portfolio_optimization/ess_potential_long_shorts_'

        # Post this Update to Slack
        # Format avg_imp_prob
        avg_imp_prob = avg_imp_prob[['deal_type', 'implied_probability']]
        avg_imp_prob['implied_probability'] = avg_imp_prob['implied_probability'].apply(lambda ip:
                                                                                        str(np.round(ip, decimals=2))
                                                                                        + " %")
        avg_imp_prob.columns = ['Deal Type', 'Implied Probability']

        slack_message('ESS_IDEA_DATABASE_ERRORS.slack',
                      {'message': message,
                       'table': tabulate(avg_imp_prob, headers='keys', tablefmt='pssql', numalign='right')},
                      channel=get_channel_name('ess_idea_db_logs'),
                      token=settings.SLACK_TOKEN)
    except Exception as e:
        print('Error in ESS Potential Long Short Tasks ... ' + str(e))
    finally:
        con.close()
        print('Connection Closed....')
