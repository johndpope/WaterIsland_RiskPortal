import datetime
from pandas.tseries.holiday import USFederalHolidayCalendar

cal = USFederalHolidayCalendar()
holidays = cal.holidays(start='2016-01-01', end='2021-12-31').to_pydatetime()


def is_market_closed():
    now = datetime.datetime.now()
    if now.weekday() in [5, 6]: return True  # weekend
    if now in holidays: return True  # holiday
    if now > datetime.datetime(now.year, now.month, now.day, 16, 0): return True  # after hours
    if now < datetime.datetime(now.year, now.month, now.day, 9, 30): return True  # before hours
    return False
