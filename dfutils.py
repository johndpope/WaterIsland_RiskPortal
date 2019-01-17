import itertools
import pandas as pd
import numpy as np
import math
import datetime
import dbutils

class df_slicer:
    def __init__(self, as_of_date=None):
        #today = datetime.date.today() if as_of_date is None else as_of_date
        #if as_of_date is None: as_of_date = today - datetime.timedelta(days=1)
        #self.today = today

        self.as_of_date = as_of_date if not pd.isnull(as_of_date) else datetime.date.today()
        self.holidays = \
            ['2015-01-01','2015-01-19','2015-02-16','2015-04-03',
             '2015-05-25','2015-07-03','2015-09-07','2015-10-12',
             '2015-11-11','2015-11-26','2015-12-25','2016-01-01',
             '2016-01-18','2016-02-15','2016-03-25','2016-05-30',
             '2016-07-04','2016-09-05','2016-11-24','2016-12-25',
             '2016-12-26',
             "2017-01-02","2017-01-16","2017-02-20","2017-04-14",
             "2017-05-29",'2017-07-04',"2017-09-04","2017-11-23",
             "2017-12-25","2018-01-01","2018-01-15","2018-02-19","2018-03-30",
             "2018-05-28","2018-07-04","2018-09-03","2018-11-22","2018-12-25"
             ]
        self.holidays_dts = [datetime.datetime.strptime(dt,'%Y-%m-%d') for dt in self.holidays]

    def slice(self, df, period):
        if period == 'MTD': return df[(df['Date'] >= self.mtd(self.prev_n_business_days(1, self.as_of_date)))]
        if period == 'QTD': return df[(df['Date'] >= self.qtd(self.prev_n_business_days(1, self.as_of_date)))]
        if period == 'YTD': return df[(df['Date'] >= self.ytd(self.prev_n_business_days(1, self.as_of_date)))]
        if period == 'ITD': return df[(df['Date'] >= self.itd(self.prev_n_business_days(1, self.as_of_date)))]
        if period == '1D': return df[(df['Date'] >= df_slicer.prev_n_business_days(self, 1,self.as_of_date) )&(df['Date'] <= self.prev_n_business_days(1,self.as_of_date))]
        if period == '3D': return df[(df['Date'] >= df_slicer.prev_n_business_days(self, 3,self.as_of_date) )&(df['Date'] <= self.prev_n_business_days(1,self.as_of_date))]
        if period == '5D': return df[(df['Date'] >= df_slicer.prev_n_business_days(self, 5,self.as_of_date) )&(df['Date'] <= self.prev_n_business_days(1,self.as_of_date))]
        if period == '30D': return df[(df['Date'] >= df_slicer.prev_n_business_days(self, 30,self.as_of_date) )&(df['Date'] <= self.prev_n_business_days(1,self.as_of_date))]

        return df

    def shift_back_if_not_business_day(self, date):
        as_of = date
        if as_of.weekday() == 5: as_of = (as_of - datetime.timedelta(days=1)) #Saturday -> Friday
        if as_of.weekday() == 6: as_of = (as_of - datetime.timedelta(days=2)) #Sunday -> Friday
        if as_of.strftime('%Y-%m-%d') in self.holidays:
            as_of = (as_of - datetime.timedelta(days=1))
            if as_of.weekday() == 5: as_of = (as_of - datetime.timedelta(days=1)) #Saturday -> Friday
            if as_of.weekday() == 6: as_of = (as_of - datetime.timedelta(days=2)) #Sunday -> Friday
        return as_of

    def shift_forward_if_not_business_day(self, date):
        as_of = date
        if as_of.weekday() == 5: as_of = (as_of + datetime.timedelta(days=2)) #Saturday -> Monday
        if as_of.weekday() == 6: as_of = (as_of + datetime.timedelta(days=1)) #Sunday -> Monday
        if as_of.strftime('%Y-%m-%d') in self.holidays:
            as_of = (as_of + datetime.timedelta(days=1))
            if as_of.weekday() == 5: as_of = (as_of + datetime.timedelta(days=2)) #Saturday -> Monday
            if as_of.weekday() == 6: as_of = (as_of + datetime.timedelta(days=1)) #Sunday -> Monday
        return as_of

    def qtd(self, date):
        return datetime.datetime(date.year, 1, 1).strftime("%Y%m%d") if date.month <= 3 else\
                    datetime.datetime(date.year, 4, 1).strftime("%Y%m%d") if date.month <= 6 else\
                    datetime.datetime(date.year, 7, 1).strftime("%Y%m%d") if date.month <= 9 else\
                    datetime.datetime(date.year, 10, 1).strftime("%Y%m%d")

    def mtd(self, date):
        return (datetime.datetime(date.year, date.month, 1)).strftime("%Y%m%d")

    def ytd(self, date):
        return (datetime.datetime(date.year, 1, 1)).strftime("%Y%m%d")

    def itd(self, date):
        return '20150101'

    def prev_n_business_days(self, n, date):
        for i in range(n):
            prev_day = df_slicer.shift_back_if_not_business_day(self, date - datetime.timedelta(1))
            date = prev_day
        return date

    def is_business_day(self, dt):
        if dt.weekday() in [5,6]: return False #weekend
        if dt in self.holidays_dts: return False #holiday
        return True


    def business_days_in_range(self, start_date, end_date):
        return sorted([start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days + 1) if self.is_business_day(start_date + datetime.timedelta(days=i))])


    def slice_date_range(self, start_date_yyyymmdd, end_date_yyyymmdd, interval_days=7):
        start_date = datetime.datetime.strptime(start_date_yyyymmdd,'%Y%m%d')
        end_date = datetime.datetime.strptime(end_date_yyyymmdd,'%Y%m%d')
        k = interval_days
        dates = []
        i=0
        while True:
            start_dt = start_date + datetime.timedelta(k*i)
            end_dt = start_date + datetime.timedelta(k*(i+1)-1)
            if end_dt >= end_date:
                end_dt = end_date
                dates.append((start_dt.strftime('%Y%m%d'),end_dt.strftime('%Y%m%d')))
                break
            dates.append((start_dt.strftime('%Y%m%d'),end_dt.strftime('%Y%m%d')))
            i+=1
        return dates

    def next_n_business_days(self, n, date):
        for i in range(n):
            next_day = df_slicer.shift_forward_if_not_business_day(self, date + datetime.timedelta(1))
            date = next_day
        return date