from contextlib import closing
from datetime import datetime

import pandas as pd
import pymssql

TODAYS_DATE = datetime.now().date().strftime('%Y-%m-%d')


class tradar:
    def __init__(self):
        pass

    @staticmethod
    def optimized_execute(query, commit=False):
        try:
            with closing(pymssql.connect(host='NYDC-WTRTRD01', user='paz', password='Welcome2', database='TradarBE')) as trdr_pnl_conn:
                with closing(trdr_pnl_conn.cursor()) as trdr_pnl_cursor:
                    trdr_pnl_cursor.execute(query)
                    if commit:
                        trdr_pnl_conn.commit()
                        return
                    fetched_res = trdr_pnl_cursor.fetchall()
                    return fetched_res
        except Exception as e:
            print(e)

    @staticmethod
    def get_position_rec():
        query = "declare @date datetime = '{todays_date}'; "\
                "declare @fundIdList varchar(max); "\
                "declare @clrIdList varchar(max) = 33; "\
                "declare @stratIdList varchar(max) = null; "\
                "select dbo.TradeFund.fund, SUM(position) as NetPosition, Sec.ticker, Sec.id "\
                "from dbo.FnNavValuationExposure(@date, 0, @fundIdList, @clrIdList, @stratIdList) Nav "\
                "inner join dbo.TradeFund with (nolock) on Nav.fundId = TradeFund.fundId "\
                "inner join dbo.TradeClr with (nolock) on Nav.clrId = TradeClr.clrId "\
                "inner join dbo.TradeStrat with (nolock) on Nav.stratId = TradeStrat.stratId "\
                "inner join dbo.Sec with (nolock) on Nav.secId = Sec.secId "\
                "inner join dbo.sectype with (nolock) on sectype.sectype = sec.sectype "\
                "left join dbo.TradeCpty with (nolock) on Nav.cptyId = TradeCpty.cptyId "\
                "left join dbo.TradeCpty OtcTradeCpty with (nolock) on Nav.otcCptyId = OtcTradeCpty.cptyId "\
                "left join dbo.GICSSector gs with (nolock) on sec.subIndustryCode = gs.subIndustryCode "\
                "left join dbo.exchange with (nolock) on exchange.exchid = sec.exchid "\
                "left join dbo.PriceHistory ph with (nolock) on ph.secId = sec.secId "\
                "and ph.pricesource = tradeFund.clientprices and ph.hdate = @date "\
                "left join secCustom with (nolock) on secCustom.userSecIndex1 = tradestrat.strat "\
                "left join dbo.sec secStrat with (nolock) on secStrat.id = secCustom.id "\
                "left join dbo.PriceHistory phSecStrat with (nolock) on phSecStrat.secId = secStrat.secId and "\
                "phSecStrat.pricesource = tradeFund.clientprices and phSecStrat.hdate = @date "\
                "left join dbo.country c with (nolock) on c.country = sec.country "\
                "left join dynamicData.TradeFundExtension tfe (nolock) on tfe.fundId = nav.fundId "\
                ", (select basefx =upper(value) from dbo.SystemCcy) [System] "\
                "where Nav.acctype < 100 "\
                "and TradeFund.entityTypeId = 0 Group by dbo.TradeFund.fund,  Sec.ticker, Sec.id;".format(todays_date=TODAYS_DATE)

        cols = ['fund', 'NetPosition', 'ticker', 'id']
        query_result = tradar.optimized_execute(query)
        tradar_df = pd.DataFrame(query_result, columns=cols)
        return tradar_df.reset_index(drop=True)
