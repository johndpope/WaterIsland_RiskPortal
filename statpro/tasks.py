from __future__ import absolute_import, unicode_literals
from celery import shared_task, current_task
import dbutils
import pandas as pd
import json
from django.db import close_old_connections

@shared_task
def get_statpro_attribution(start_date, end_date, fund_name):
    ''' Background Task for StatPro Attribution '''

    close_old_connections()
    # If by Tradegroup, then just use data from Database; If @ Fund level, further compound the Dataframe
    by_tradegroup = False
    if 'tradegroup' in str(fund_name).lower():
        by_tradegroup = True #Process @ TradeGroup level

    # Remove -By TradeGroup from fund_name
    fund_name = fund_name.replace("- By TradeGroup", "")
    statpro_attribution_df = dbutils.Wic.get_statpro_attribution(fund_name, start_date, end_date) #Convert to Numeric
    statpro_attribution_df = statpro_attribution_df.apply(pd.to_numeric, errors='ignore')

    fund_level_df = statpro_attribution_df.copy()

    if statpro_attribution_df.empty:
        #No Data Available
        return'No Data Available'

    # Process at TradeGroup Level
    final_dataframe = pd.DataFrame(columns=['TradeGroup', 'Compounded Contribution', 'From', 'To'])
    unique_tradegroups = statpro_attribution_df['Classification3Name'].unique()

    for tradegroup in unique_tradegroups:
        filtered_dataframe = statpro_attribution_df[statpro_attribution_df.Classification3Name == tradegroup]['Ctp']
        min_date = statpro_attribution_df[statpro_attribution_df.Classification3Name == tradegroup]['From'].min()
        max_date = statpro_attribution_df[statpro_attribution_df.Classification3Name == tradegroup]['To'].max()
        first_value = float(filtered_dataframe.iloc[0])
        first_value = first_value / 100  # Initially Divide by 100
        compounded_ctp = first_value
        for item in filtered_dataframe[1:]:
            compounded_ctp = (1 + float(item) / 100) * (1 + compounded_ctp) - 1
        compounded_ctp *= 10000
        df2 = pd.DataFrame([[tradegroup, compounded_ctp, str(min_date), str(max_date)]],
                           columns=['TradeGroup', 'Compounded Contribution', 'From', 'To'])

        final_dataframe = final_dataframe.append(df2)

    if by_tradegroup:
        return json.dumps(json.loads(final_dataframe.to_json(orient='records',date_format='iso',date_unit='s')))
    else:
        #Process @ Fund Level
        unique_dates = statpro_attribution_df['From'].unique()
        summation_df = pd.DataFrame(columns=['Fund','Sum of Contributions','From'])
        for each_date in unique_dates:
            df_sum = pd.DataFrame([[fund_name,statpro_attribution_df.loc[statpro_attribution_df['From'] == each_date]['Ctp'].sum(),each_date]],columns=['Fund','Sum of Contributions','From'])
            summation_df = summation_df.append(df_sum)

        summation_df['From'] = pd.to_datetime(summation_df['From'])
        minimum_year = summation_df['From'].min().year
        maximumm_year = summation_df['From'].max().year
        fund_level_dataframe = pd.DataFrame(columns=['TradeGroup', 'Compounded Contribution', 'From', 'To'])
        for year in range(minimum_year, maximumm_year+1):
            # Process for each month. First get the minimum and maximum months in each Year
            minimum_month = summation_df.loc[summation_df['From'].dt.year == year]['From'].min().month
            maximum_month = summation_df.loc[summation_df['From'].dt.year == year]['From'].max().month
            for month in range(minimum_month,maximum_month+1):
                #Process for Each month
                monthly_df = summation_df.loc[(summation_df['From'].dt.month==month) & (summation_df['From'].dt.year==year)]
                first_value = monthly_df['Sum of Contributions'].iloc[0]
                compounded_ctp = first_value / 100
                min_date = monthly_df['From'].min()
                max_date = monthly_df['From'].max()
                for tradegroup_contribution in monthly_df['Sum of Contributions'][1:]:  # Already Unique
                    compounded_ctp = (1 + tradegroup_contribution / 100) * (1 + compounded_ctp) - 1

                compounded_ctp *= 10000
                fund_level_dataframe = fund_level_dataframe.append(pd.DataFrame([[fund_name, compounded_ctp, str(min_date).replace("00:00:00",""), str(max_date).replace("00:00:00","")]],
                                                    columns=['TradeGroup', 'Compounded Contribution', 'From', 'To']))

        return json.dumps(json.loads(fund_level_dataframe.to_json(orient='records', date_format='iso', date_unit='s')))

    # print(statpro_attribution_df.loc[statpro_attribution_df['From'].getYear == each_date)
    # Compound Summation Df to get Fund level Attribution
    first_value = summation_df['Sum of Contributions'].iloc[0]
    compounded_ctp = first_value / 100
    min_date = fund_level_df['From'].min()
    max_date = fund_level_df['To'].max()
    for tradegroup_contribution in summation_df['Sum of Contributions'][1:]:  # Already Unique
        compounded_ctp = (1 + tradegroup_contribution / 100) * (1 + compounded_ctp) - 1

    compounded_ctp *= 10000
    fund_level_dataframe = pd.DataFrame([[fund_name, compounded_ctp, str(min_date), str(max_date)]],
                                        columns=['TradeGroup', 'Compounded Contribution', 'From', 'To'])

    return json.dumps(json.loads(fund_level_dataframe.to_json(orient='records', date_format='iso', date_unit='s')))