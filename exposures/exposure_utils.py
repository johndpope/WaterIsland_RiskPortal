import pandas as pd
import json
import datetime
from django.db.models import Max, Min
from .models import ExposuresSnapshot


def get_exposure_dataframe(as_of_yyyy_mm_dd=None):
    response = {}
    max_date = datetime.datetime.now().date()
    min_date = ExposuresSnapshot.objects.all().aggregate(Min('date'))['date__min']

    if as_of_yyyy_mm_dd is None:
        as_of_yyyy_mm_dd = ExposuresSnapshot.objects.all().aggregate(Max('date'))['date__max'].strftime('%Y-%m-%d')

    else:
        if datetime.datetime.strptime(as_of_yyyy_mm_dd, '%Y-%m-%d').date() < min_date:
            return 'DateError', as_of_yyyy_mm_dd, min_date, max_date

    min_date = min_date.strftime('%Y-%m-%d')
    max_date = max_date.strftime('%Y-%m-%d')
    funds_exp_df = pd.DataFrame.from_records(list(ExposuresSnapshot.objects.filter(date=as_of_yyyy_mm_dd).values()))
    if len(funds_exp_df) == 0:
        return 'No Data Found', as_of_yyyy_mm_dd, min_date, max_date

    def create_story_url(row):
            url = '../position_stats/get_tradegroup_story?TradeGroup='+row['tradegroup']+'&Fund='+row['fund']
            return "<a target='_blank' href='"+url+"'>View</a>"

    funds_exp_df['StoryLink'] = funds_exp_df.apply(create_story_url, axis=1)
    funds_exp_df['date'] = funds_exp_df['date'].apply(str)
    funds = funds_exp_df['fund'].unique()

    for fund_code in funds:
        f_exp_df = funds_exp_df[funds_exp_df['fund'] == fund_code]
        f_slv_exp = f_exp_df.groupby(['date', 'fund', 'sleeve', 'longshort']).sum().reset_index()
        response[fund_code] = []
        response[fund_code].append({'All Sleeves': f_slv_exp.to_json(orient='records')})

        sleeves = f_exp_df['sleeve'].unique()
        for slv in sleeves:
            slv_df = f_exp_df[f_exp_df['sleeve'] == slv].sort_values(by=['sleeve', 'bucket'])
            slv_long_df = slv_df[slv_df['longshort'] == 'Long'].sort_values(by=['sleeve', 'bucket'])
            slv_short_df = slv_df[slv_df['longshort'] == 'Short'].sort_values(by=['sleeve', 'bucket'])
            slv_summary_df = slv_df.groupby(['date', 'sleeve', 'bucket', 'longshort']).sum().reset_index().sort_values(
                by=['sleeve', 'bucket'])

            del slv_long_df['fund']
            del slv_long_df['sleeve']
            del slv_short_df['fund']
            del slv_short_df['sleeve']
            del slv_summary_df['sleeve']

            response[fund_code].append({slv: [
                {'Total': slv_summary_df.to_json(orient='records')},
                {'Long': slv_long_df.to_json(orient='records')},
                {'Short': slv_short_df.to_json(orient='records')}
            ]})


    return json.dumps(response), as_of_yyyy_mm_dd, min_date, max_date

