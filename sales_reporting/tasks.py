import os
import pandas as pd
import django
from django.conf import settings
import datetime
from threading import Thread
from email_utilities import send_email2
from celery import shared_task
from sqlalchemy import create_engine
from .render import *
import dbutils
import dfutils

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
django.setup()


@shared_task
def email_weekly_sales_report():
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                           + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)

    con = engine.connect()
    pd.set_option('display.float_format', lambda x: '%.3f' % x)
    bps_attributions = pd.read_sql_query("SELECT `Date`, Fund, SUM(YTD_bps), SUM(QTD_bps) FROM " \
                                         "wic.tradegroup_attribution_to_fund_nav_bps " \
                                         "where `Date` = (SELECT MAX(`Date`) FROM wic.tradegroup_attribution_to_fund_nav_bps) " \
                                         "GROUP BY `Date`, Fund", con=con)

    dollar_attributions = pd.read_sql_query("SELECT `Date`, Fund, SUM(YTD_Dollar), SUM(QTD_Dollar) FROM " \
                                            "wic.tradegroup_attribution_to_fund_nav_dollar " \
                                            "where `Date` = (SELECT MAX(`Date`) FROM wic.tradegroup_attribution_to_fund_nav_dollar) " \
                                            "GROUP BY `Date`, Fund", con=con)
    bps_attributions.columns = ['Date', 'Fund', 'YTD (bps)', 'QTD (bps)']
    dollar_attributions.columns = ['Date', 'Fund', 'YTD ($)', 'QTD ($)']

    pivoted_bps_attributions = pd.pivot_table(bps_attributions, columns=['Fund'])
    pivoted_bps_attributions.columns.name = ' '
    pivoted_dollar_attributions = pd.pivot_table(dollar_attributions, columns=['Fund'])
    pivoted_dollar_attributions.columns.name = ' '
    pivoted_bps_attributions = pivoted_bps_attributions.round(decimals=2)
    pivoted_dollar_attributions = pivoted_dollar_attributions.round(decimals=2)

    def color_negative_red(val):
        if val < 0:
            color = 'red'
        else:
            color = 'green'

        return 'color: %s' % color

    styles = [
        {'selector': 'tr:hover td', 'props': [('background-color', 'yellow')]},
        {'selector': 'th, td', 'props': [('border', '1px solid black'),
                                         ('padding', '12px'),
                                         ('text-align', 'center')]},
        {'selector': 'th', 'props': [('font-weight', 'bold')]},
        {'selector': '', 'props': [('border-collapse', 'collapse'),
                                   ('border', '1px solid black'),
                                   ('margin', '0 auto')]}
    ]

    pivoted_bps_attributions = pivoted_bps_attributions.style.applymap(color_negative_red,
                                                                       ).set_table_styles(styles)

    pivoted_dollar_attributions = pivoted_dollar_attributions.style.applymap(color_negative_red,
                                                                             ).set_table_styles(styles)
    aed_bucket_weightings = pd.read_sql_query("SELECT `date`, fund, Bucket, SUM(alpha_exposure) FROM "
                                              "prod_wic_db.exposures_exposuressnapshot "
                                              "WHERE `date` = (SELECT MAX(`date`) FROM prod_wic_db.exposures_exposuressnapshot) "
                                              "AND fund LIKE 'AED' "
                                              "GROUP BY `date`, fund, bucket", con=con)

    aed_bucket_weightings = aed_bucket_weightings.round(decimals=2)
    del aed_bucket_weightings['date']
    del aed_bucket_weightings['fund']
    aed_bucket_weightings.columns = ['Bucket', 'Alpha Exposure']
    aed_bucket_weightings['Alpha Exposure'] = aed_bucket_weightings['Alpha Exposure'].apply(lambda x: str(x) + " %")
    pivoted_aed_bucket_weightings = pd.pivot_table(aed_bucket_weightings, columns=['Bucket'], aggfunc='first')
    pivoted_aed_bucket_weightings.columns.name = ' '
    pivoted_aed_bucket_weightings = pivoted_aed_bucket_weightings.style.set_table_styles(styles)

    # Buckets Contribution Section
    import dfutils
    aed_buckets_performance = pd.read_sql_query("SELECT * FROM wic.buckets_snapshot where Fund like 'AED' ", con=con)

    aed_buckets_performance['EndDate'] = aed_buckets_performance['EndDate'].apply(
        lambda x: x if x is None else pd.to_datetime(x).strftime('%Y-%m-%d'))
    aed_buckets_performance['InceptionDate'] = aed_buckets_performance['InceptionDate'].apply(
        lambda x: x if x is None else pd.to_datetime(x).strftime('%Y-%m-%d'))

    metrics2include = [('P&L(bps)', 'YTD'), ('P&L($)', 'YTD'),
                       ('P&L(bps)', 'QTD'), ('P&L($)', 'QTD'),
                       ]

    metric2display_name = {'P&L(bps)': '', 'P&L($)': ''}
    metric2unit = {'P&L(bps)': 'bps', 'P&L($)': '$'}

    metrics_df = pd.DataFrame([dfutils.json2row(json) for json in aed_buckets_performance['Metrics in NAV JSON']])
    metrics_df.index = aed_buckets_performance.index

    for (metric, period) in metrics2include:
        unit = metric2unit[metric]
        disp_name = metric2display_name[metric]
        display_colname = disp_name + ' ' + period + '(' + unit + ')'
        aed_buckets_performance[display_colname] = metrics_df[metric + '|' + period]

    del aed_buckets_performance['Metrics in NAV JSON'];
    del aed_buckets_performance['Metrics in NAV notes JSON']
    del aed_buckets_performance['Metrics in Bet JSON'];
    del aed_buckets_performance['Metrics in Bet notes JSON']

    aed_buckets_performance = aed_buckets_performance[(~pd.isnull(aed_buckets_performance[' YTD($)']))]

    base_cols = ['Fund', 'Bucket', 'InceptionDate', 'EndDate']
    bps_cols = [' YTD(bps)', ' QTD(bps)']
    dollar_cols = [' YTD($)', ' QTD($)']
    aed_buckets_bps_df = aed_buckets_performance[base_cols + bps_cols].sort_values(by=' YTD(bps)')
    aed_buckets_bps_df.rename(columns={' YTD(bps)': 'YTD_bps', ' QTD(bps)': 'QTD_bps'}, inplace=True)
    aed_buckets_dollar_df = aed_buckets_performance[base_cols + dollar_cols].sort_values(by=' YTD($)')
    aed_buckets_dollar_df.rename(columns={' YTD($)': 'YTD_Dollar', ' QTD($)': 'QTD_Dollar'}, inplace=True)

    del aed_buckets_bps_df['Fund']
    pivoted_aed_buckets_bps_df = pd.pivot_table(aed_buckets_bps_df, columns=['Bucket'])

    del aed_buckets_dollar_df['Fund']
    pivoted_aed_buckets_dollar_df = pd.pivot_table(aed_buckets_dollar_df, columns=['Bucket'])

    pivoted_aed_buckets_bps_df = pivoted_aed_buckets_bps_df.style.applymap(color_negative_red,
                                                                           ).set_table_styles(styles)
    pivoted_aed_buckets_dollar_df = pivoted_aed_buckets_dollar_df.style.applymap(color_negative_red,
                                                                                 ).set_table_styles(styles)

    # P&L Monitors Section
    df = pd.read_sql_query("SELECT * FROM " + settings.CURRENT_DATABASE + ".realtime_pnl_impacts_pnlmonitors"
                                                                          " where last_updated = "
                                                                          "(select max(last_updated) from "
                           + settings.CURRENT_DATABASE + ".realtime_pnl_impacts_pnlmonitors)",
                           con=con)

    # Close Connection
    con.close()
    del df['last_updated']
    df.rename(columns={'fund': 'Fund', 'ytd_active_deal_losses': 'YTD Active Deal Losses',
                       'ytd_closed_deal_losses': 'YTD Closed Deal Losses', 'ann_loss_budget_perc': 'Loss Budget',
                       'investable_assets': 'AUM', 'gross_ytd_pnl': 'Gross YTD P&L',
                       'ann_gross_pnl_target_perc': 'Ann. Gross P&L Target %', 'time_passed': 'Time Passed',
                       'gross_ytd_return': 'Gross YTD Return',
                       'ann_gross_pnl_target_dollar': 'Ann. Gross P&L Target $',
                       'ytd_pnl_perc_target': 'YTD P&L % of Target', 'ann_loss_budget_dollar': 'Ann Loss Budget $',
                       'ytd_total_loss_perc_budget': 'YTD Total Loss % of Budget'}, inplace=True)

    pivoted = pd.pivot_table(df, columns=['Fund'], aggfunc=lambda x: x, fill_value='')

    pivoted = pivoted[['ARB', 'MACO', 'MALT', 'AED', 'CAM', 'LG', 'LEV', 'TACO', 'TAQ']]
    pivoted = pivoted.reindex(['AUM',
                               'Ann. Gross P&L Target %',
                               'Gross YTD Return',
                               'YTD P&L % of Target',
                               'Time Passed',
                               'Ann. Gross P&L Target $',
                               'Gross YTD P&L',
                               'Loss Budget',
                               'YTD Total Loss % of Budget',
                               'Time Passed',
                               'Ann Loss Budget $',
                               'YTD Closed Deal Losses',
                               'YTD Active Deal Losses',
                               ])
    df1 = pivoted.iloc[:7].copy()
    df2 = pivoted.iloc[7:].copy()
    df3 = pd.DataFrame([list(pivoted.columns.values)], columns=list(pivoted.columns.values))
    df1 = df1.append(df3)
    df1.index.values[5] = '* Ann. Gross P&L Target $'
    df1.index.values[7] = 'Loss Budgets'
    df1 = df1.append(df2)
    df1.index.values[8] = 'Ann Loss Budget %'
    df1.index.values[0] = 'Investable Assets'
    df1.index.values[4] = 'Time Passed%'
    df1.index.values[10] = 'Time Passed %'
    df1.index.values[11] = '* Ann Loss Budget $'

    df1 = df1.style.set_table_styles(styles)

    # Winners/Losers
    tg_snapshot_df = dbutils.Wic.get_tradegroups_snapshot()

    aed_qtd_winners, aed_qtd_losers, aed_ytd_winners, aed_ytd_losers, aed_ytd_active_winners, aed_ytd_active_losers = get_fund_winners_losers(
        tg_snapshot_df, 'AED')

    arb_qtd_winners, arb_qtd_losers, arb_ytd_winners, arb_ytd_losers, arb_ytd_active_winners, arb_ytd_active_losers = get_fund_winners_losers(
        tg_snapshot_df, 'ARB')

    taco_qtd_winners, taco_qtd_losers, taco_ytd_winners, taco_ytd_losers, taco_ytd_active_winners, taco_ytd_active_losers = get_fund_winners_losers(
        tg_snapshot_df, 'TACO')

    aed_qtd_winners = aed_qtd_winners.style.set_table_styles(styles)
    aed_qtd_losers = aed_qtd_losers.style.set_table_styles(styles)
    aed_ytd_winners = aed_ytd_winners.style.set_table_styles(styles)
    aed_ytd_losers = aed_ytd_losers.style.set_table_styles(styles)
    aed_ytd_active_winners = aed_ytd_active_winners.style.set_table_styles(styles)
    aed_ytd_active_losers = aed_ytd_active_losers.style.set_table_styles(styles)

    arb_qtd_winners = arb_qtd_winners.style.set_table_styles(styles)
    arb_qtd_losers = arb_qtd_losers.style.set_table_styles(styles)
    arb_ytd_winners = arb_ytd_winners.style.set_table_styles(styles)
    arb_ytd_losers = arb_ytd_losers.style.set_table_styles(styles)
    arb_ytd_active_winners = arb_ytd_active_winners.style.set_table_styles(styles)
    arb_ytd_active_losers = arb_ytd_active_losers.style.set_table_styles(styles)

    taco_qtd_winners = taco_qtd_winners.style.set_table_styles(styles)
    taco_qtd_losers = taco_qtd_losers.style.set_table_styles(styles)
    taco_ytd_winners = taco_ytd_winners.style.set_table_styles(styles)
    taco_ytd_losers = taco_ytd_losers.style.set_table_styles(styles)
    taco_ytd_active_winners = taco_ytd_active_winners.style.set_table_styles(styles)
    taco_ytd_active_losers = taco_ytd_active_losers.style.set_table_styles(styles)

    params = {'bps_attributions': pivoted_bps_attributions.render(),
              'dollar_attributions': pivoted_dollar_attributions.render(),
              'aed_bucket_weightings': pivoted_aed_bucket_weightings.render(),
              'pnl_monitors': df1.render(),
              'buckets_contribution_bps': pivoted_aed_buckets_bps_df.render(),
              'buckets_contribution_dollar': pivoted_aed_buckets_dollar_df.render(),
              'aed_qtd_winners': aed_qtd_winners.hide_index().render(), 'aed_qtd_losers': aed_qtd_losers.hide_index().render(),
              'aed_ytd_winners': aed_ytd_winners.hide_index().render(),
              'aed_ytd_losers': aed_ytd_losers.hide_index().render(), 'aed_ytd_active_winners': aed_ytd_active_winners.hide_index().render(),
              'aed_ytd_active_losers': aed_ytd_active_losers.hide_index().render(), 'arb_qtd_winners': arb_qtd_winners.hide_index().render(),
              'arb_qtd_losers': arb_qtd_losers.hide_index().render(), 'arb_ytd_winners': arb_ytd_winners.hide_index().render(),
              'arb_ytd_losers': arb_ytd_losers.hide_index().render(),
              'arb_ytd_active_winners': arb_ytd_active_winners.hide_index().render(),
              'arb_ytd_active_losers': arb_ytd_active_losers.hide_index().render(),
              'taco_qtd_winners': taco_qtd_winners.hide_index().render(), 'taco_qtd_losers': taco_qtd_losers.hide_index().render(),
              'taco_ytd_winners': taco_ytd_winners.hide_index().render(),
              'taco_ytd_losers': taco_ytd_losers.hide_index().render(),
              'taco_ytd_active_winners': taco_ytd_active_winners.hide_index().render(),
              'taco_ytd_active_losers': taco_ytd_active_losers.hide_index().render(),
              }

    file = Render.render_to_file('sales_weekly_template.html', params)
    thread = Thread(target=send_email2, args=(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD,
                                              ['kgorde@wicfunds.com'],
                                              "Weekly Sales Report - " + datetime.datetime.now().strftime('%Y-%m-%d'),
                                              'dispatch@wicfunds.com',
                                              'Please find attached Weekly Sales Report!', file))
    thread.start()

    return "Completed Task - (Weekly Sales Reporting)"


def get_fund_winners_losers(tg_snapshot_df, fund_code):
    f_df = tg_snapshot_df[tg_snapshot_df['Fund'] == fund_code].copy()
    metrics_df = pd.DataFrame([dfutils.json2row(json) for json in f_df['Metrics in NAV JSON']])
    metrics_df.index = f_df.index
    f_df['YTD(bps)'] = metrics_df['P&L(bps)|YTD'];
    f_df['YTD($)'] = metrics_df['P&L($)|YTD']
    f_df['QTD(bps)'] = metrics_df['P&L(bps)|QTD'];
    f_df['QTD($)'] = metrics_df['P&L($)|QTD']

    tg_ytd_df = f_df[~pd.isnull(f_df['YTD(bps)'])][
        ['TradeGroup', 'InceptionDate', 'EndDate', 'Status', 'YTD(bps)', 'YTD($)']].sort_values(by='YTD(bps)',
                                                                                                ascending=False).rename(
        columns={'YTD(bps)': 'bps', 'YTD($)': '$'})
    active_tg_ytd_df = tg_ytd_df[tg_ytd_df['Status'] == 'ACTIVE'].sort_values(by='bps', ascending=False)
    tg_qtd_df = f_df[~pd.isnull(f_df['QTD(bps)'])][
        ['TradeGroup', 'InceptionDate', 'EndDate', 'Status', 'QTD(bps)', 'QTD($)']].sort_values(by='QTD(bps)',
                                                                                                ascending=False).rename(
        columns={'QTD(bps)': 'bps', 'QTD($)': '$'})

    qtd_winners = tg_qtd_df.head(5)
    qtd_losers = tg_qtd_df.tail(5)

    ytd_winners = tg_ytd_df.head(5)
    ytd_losers = tg_ytd_df.tail(5)

    ytd_active_winners = active_tg_ytd_df.head(5)
    ytd_active_losers = active_tg_ytd_df.tail(5)

    return qtd_winners, qtd_losers, ytd_winners, ytd_losers, ytd_active_winners, ytd_active_losers
