import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
import pandas as pd
import bbgclient
import dbutils
import pandas as pd
from django.db import connection
from django.conf import settings

#Following Task should Run periodically (every morning at 9.45am to capture live data and report the NAV Impacts for each Tradegroup)
def pnl_calculations():
    ''' Fetch all the positions from last Flat file and populate the model which updates daily... '''
    #Fetch latest positions
    latest_positions_df = dbutils.Wic.get_latest_positions_for_nav_impacts()
    api_host = bbgclient.bbgclient.get_next_available_host()
    bloomberg_ids = list(latest_positions_df['BloombergID'].fillna('NA'))

    live_price_df = pd.DataFrame.from_dict(bbgclient.bbgclient.get_secid2field(bloomberg_ids, 'BBGIDS', ['CRNCY_ADJ_PX_LAST'],req_type='refdata', api_host=api_host), orient='index').reset_index()
    #distinct bloomberg Ids are fewer than securities....Left merge

    live_price_df['CRNCY_ADJ_PX_LAST'] = live_price_df['CRNCY_ADJ_PX_LAST'].apply(lambda x: x[0])
    live_price_df.columns = ['BloombergID', 'LAST_PX']

    #Merge with Latest_positions_df
    latest_positions_df = pd.merge(latest_positions_df, live_price_df, how='left', on='BloombergID')

    #Clean up
    #If last_px is none, take the price from Eze
    latest_positions_df['LAST_PX'] = latest_positions_df['LAST_PX'].fillna(latest_positions_df['Price'])



#pnl_calculations()


'''Should run each morning'''
def update_positions_for_downside_formulae_merger_arb():
    '''Adds new Positions for Formulae based Downsides '''
    api_host = bbgclient.bbgclient.get_next_available_host()
    df = pd.read_sql_query('call wic.GET_POSITIONS_FOR_DOWNSIDE_FORMULAE()', con=connection)
    df.index.names = ['id']
    df.rename(columns={'TG':'TradeGroup'}, inplace=True)
    #Remaining Fields to be Added are the following: 1. LastUpdate 2.IsExcluded 3. DownsideType 4. ReferenceDataPoint
    #5. ReferencePrice 6.Operation 7. CustomInput 8.Outlier 9. cix_ticker

    cols2merge = ['TradeGroup', 'Underlying']

    #Uncomment below for initial merge..
    # df['LastUpdate'] = None
    # df['IsExcluded'] = 'No'
    # df['BaseCaseCustomInput'] = None
    # df['BaseCaseReferenceDataPoint'] = None
    # df['BaseCaseReferencePrice'] = None
    # df['BaseCaseOperation'] = None
    # df['BaseCaseDownsideType'] = None
    # df['outlier'] = None
    # df['cix_ticker'] = None
    # df['OutlierCustomInput'] = None
    # df['OutlierDownsideType'] = None
    # df['OutlierOperation'] = None
    # df['OutlierReferenceDataPoint'] = None
    # df['OutlierReferencePrice'] = None
    # df['base_case'] = None
    # df['base_case_notes'] = None
    # df['outlier_notes'] = None

    df['Underlying'] = df['Underlying'].apply(lambda x: x.upper() + " EQUITY")
    all_unique_tickers = list(df['Underlying'].unique())
    live_price_df = pd.DataFrame.from_dict(bbgclient.bbgclient.get_secid2field(all_unique_tickers, 'tickers', ['PX_LAST'], req_type='refdata',api_host=api_host), orient='index').reset_index()
    live_price_df['PX_LAST'] = live_price_df['PX_LAST'].apply(lambda x: x[0])
    live_price_df.columns = ['Underlying', 'PX_LAST']

    #Merge Live Price Df
    df = pd.merge(df, live_price_df, how='left', on=['Underlying'])




    #Delete the old LastPrice
    del df['LastPrice']

    df.rename(columns={'PX_LAST': 'LastPrice'}, inplace=True)
    #uncomment below for New inserts
    #
    # df.reset_index(inplace=True)
    # df.rename(columns={'index':'id'}, inplace=True)
    #
    # df.to_sql(name='risk_reporting_formulaebaseddownsides', con=con, if_exists='append', index=False,
    #           schema=settings.CURRENT_DATABASE)
    # exit(1)

    #Exclude the Current Positions
    current_df = pd.read_sql_query('Select * from '+settings.CURRENT_DATABASE+'.risk_reporting_formulaebaseddownsides', con=connection)
    #     # Perform an Outer Merge on current and new df on Underlying and Tradegroup....After that delete the previous Risklimit and DealValue
    current_df = pd.merge(current_df, df, how='outer', on=cols2merge).reset_index().drop(columns=['id']).rename(columns={'index':'id'})

    # Delete all deals that are in CurrentDF but not present in the New DF (these are the closed positions)
    current_df = current_df[current_df['TradeGroup'].isin(df['TradeGroup'])]

    current_df.rename(columns={'DealValue_y':'DealValue', 'LastPrice_y':'LastPrice', 'RiskLimit_y':'RiskLimit', 'TargetAcquirer_y':'TargetAcquirer', 'Analyst_y':'Analyst', 'OriginationDate_y':'OriginationDate'}, inplace=True)
    #Delete the Old values...
    del current_df['DealValue_x']
    del current_df['LastPrice_x']
    del current_df['RiskLimit_x']
    del current_df['TargetAcquirer_x']
    del current_df['Analyst_x']
    del current_df['OriginationDate_x']

    current_df.drop_duplicates(['TradeGroup', 'Underlying', 'Analyst'], inplace=True)
    current_df['IsExcluded'] = current_df['IsExcluded'].apply(lambda x: 'No' if pd.isnull(x) else x)

    #Truncate the Current downsides table
    connection.cursor().execute('SET FOREIGN_KEY_CHECKS=0;TRUNCATE TABLE '+settings.CURRENT_DATABASE+'.risk_reporting_formulaebaseddownsides')

    current_df.to_sql(name='risk_reporting_formulaebaseddownsides', con=settings.SQLALCHEMY_CONNECTION, if_exists='append', index=False, schema=settings.CURRENT_DATABASE)
    #Export only the Excluded ones
    print('Done Exporting new Deals')



'''Should Run Every 30 mins...'''
def update_live_price_of_formula_based_downsides_positions():
    api_host = bbgclient.bbgclient.get_next_available_host()
    df = pd.read_sql_query('Select * from '+settings.CURRENT_DATABASE+'.risk_reporting_formulaebaseddownsides', con=connection)
    all_unique_tickers = list(df['Underlying'].apply(lambda x: x.upper() + " EQUITY").unique())
    live_price_df = pd.DataFrame.from_dict(
        bbgclient.bbgclient.get_secid2field(all_unique_tickers, 'tickers', ['PX_LAST'], req_type='refdata',
                                            api_host=api_host), orient='index').reset_index()
    live_price_df['PX_LAST'] = live_price_df['PX_LAST'].apply(lambda x: x[0])
    live_price_df.columns = ['Underlying', 'PX_LAST']

    #Before Merging, Remove EQUTIY from live Price Dataframe

    live_price_df['Underlying'] = live_price_df['Underlying'].apply(lambda x:x.rsplit(' ',1)[0])


    # Merge Live Price Df
    df = pd.merge(df, live_price_df, how='left', on=['Underlying'])
    # Delete the old LastPrice
    del df['LastPrice']
    df.rename(columns={'PX_LAST': 'LastPrice'}, inplace=True)
    df.to_sql(name='risk_reporting_formulaebaseddownsides', con=settings.SQLALCHEMY_CONNECTION, if_exists='replace', index=False, schema=settings.CURRENT_DATABASE)
    print('Updated Live Prices of Formula Based Downsides')


#update_positions_for_downside_formulae_merger_arb()