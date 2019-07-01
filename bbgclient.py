__author__ = 'kgorde'
import json
import datetime
import dbutils

import urllib.request
import pandas as pd



class bbgclient:
    def __init__(self):
        pass

    @staticmethod
    def try_ping_host(host):
        tested_security = 'SPX Index'
        res = bbgclient.get_secid2field([tested_security],'tickers',['PX_LAST'],req_type='refdata',api_host=host)
        if tested_security not in res: return False
        if pd.isnull(res[tested_security]): return False
        if 'PX_LAST' not in res[tested_security]: return False
        if len(res[tested_security]['PX_LAST']) == 0: return False
        if pd.isnull(res[tested_security]['PX_LAST'][0]): return False
        return True

    @staticmethod
    def get_next_available_host():
        #dbutils.wic.log('BLOOMBERG API','Looking up next available API server')
        # host = 'esansone-nb'
        # if bbgclient.try_ping_host(host):
        #     return host
        # dbutils.wic.log('BLOOMBERG API','esansone-nb seems to be down')

        host = '192.168.0.15:8080'
        if bbgclient.try_ping_host(host):
            return host


        return 'None'

    @staticmethod
    def get_ticker2intra_day_vwap(tickers, date_yyyymmdd, start_time, end_time, api_host=None):
        if api_host is None: api_host = bbgclient.get_next_available_host()
        url = "http://"+api_host+"/wic/api/v1.0/vwaps_by_ticker?tickers=" + ",".join([str(id) for id in tickers]) + "&date="+ date_yyyymmdd+ "&start_time="+ start_time+ "&end_time="+ end_time
        print(url)
        url = url.replace(" ","%20")
        ticker2vwap = {tkr:None for tkr in tickers}
        try:
            with urllib.request.urlopen(url) as resp:
                html = resp.read().decode()

            parsed_json = json.loads(html)
            results = parsed_json[list(parsed_json.keys())[0]]
            for res in results:
                for tkr in res:
                    if tkr not in ticker2vwap:
                        continue # error in bloomberg-vm api
                    tkr_data = res[tkr]
                    if "EQY_WEIGHTED_AVG_PX" not in tkr_data["fields"]:
                        continue
                    ticker2vwap[tkr] = float(tkr_data["fields"]["EQY_WEIGHTED_AVG_PX"][0])
        except:
            pass
        finally:
            return ticker2vwap

    @staticmethod
    def get_bbgid2vwap(bbgids, start_date,end_date,api_host=None):
        if api_host is None: api_host = bbgclient.get_next_available_host()
        start_date_yyyymmdd = datetime.datetime.strptime(start_date, '%Y-%m-%d').strftime('%Y%m%d')
        end_date_yyyymmdd = datetime.datetime.strptime(end_date, '%Y-%m-%d').strftime('%Y%m%d')
        url = "http://"+api_host+"/wic/api/v1.0/vwaps?bbgids=" + ",".join([str(id) for id in bbgids]) + "&start_date="+ start_date_yyyymmdd +"&end_date=" + end_date_yyyymmdd
        bbgid2vwap = {bbgid:None for bbgid in bbgids}
        try:
            with urllib.request.urlopen(url) as resp:
                html = resp.read().decode()

            parsed_json = json.loads(html)
            results = parsed_json[list(parsed_json.keys())[0]]
            for res in results:
                for key in res:
                    bbgid = str(key.split('/bbgid/')[1])
                    if bbgid not in bbgid2vwap:
                        continue # error
                    bbgid_data = res[key]
                    if "EQY_WEIGHTED_AVG_PX" not in bbgid_data["fields"]:
                        continue
                    bbgid2vwap[bbgid] = float(bbgid_data["fields"]["EQY_WEIGHTED_AVG_PX"][0])
        except:
            pass
        finally:
            return bbgid2vwap

    @staticmethod
    def get_secid2hp(secids,secid_type, start_date, end_date,api_host=None):
        if api_host is None: api_host = bbgclient.get_next_available_host()
        """gets mapping from bbgid to its historical prices. start and end dates are in yyyymmdd format.
        secid_type can be bbgids or tickers"""
        url = "http://"+api_host+"/wic/api/v1.0/hp_"+secid_type+"?"+secid_type+"=" + ",".join([str(id) for id in secids]) + "&start_date=" + start_date + "&end_date=" + end_date
        url = url.replace(" ","%20")
        secid2hp = {secid:{"Prices": [], "Dates": []} for secid in secids}
        try:
            with urllib.request.urlopen(url) as resp:
                html = resp.read().decode()

            parsed_json = json.loads(html)
            results = parsed_json[list(parsed_json.keys())[0]]
            for res in results:
                for key in res:
                    secid = str(key.split('/bbgid/')[1]) if secid_type == "bbgid" else key
                    if secid not in secid2hp:
                        continue # error in bloomberg-vm api
                    bbgid_data = res[key]
                    if "PX_LAST" not in bbgid_data["fields"]:
                        secid2hp[secid]["Prices"].append(None)
                        secid2hp[secid]["Dates"].append(None)
                        continue
                    for prc in bbgid_data["fields"]["PX_LAST"]:
                        secid2hp[secid]["Prices"].append(prc)
                    for date in bbgid_data["fields"]["date"]:
                        secid2hp[secid]["Dates"].append(date)
        except Exception as e:
            print('exception in bbgclient.get_secid2hp for secids ' + ",".join(secids) + str(e.message))
            #
        finally:
            return secid2hp

    @staticmethod
    def get_timeseries(ticker,mnemonic,start_date_yyyymmdd,end_date_yyyymmdd,overrides_dict={}, api_host=None):
        if api_host is None: api_host = bbgclient.get_next_available_host()
        secid2fields = bbgclient.get_secid2field([ticker], "tickers",[mnemonic,"date"], start_date_yyyymmdd, end_date_yyyymmdd, overrides_dict, "histdata", api_host)

        if len(secid2fields[ticker]["date"]) != len(secid2fields[ticker][mnemonic]):
            # print('WARNING: ' + ticker + ' for ' + mnemonic + ' between ' + start_date_yyyymmdd + ' and ' + end_date_yyyymmdd + ' return mismatch date-value')
            return pd.Series(secid2fields[ticker][mnemonic],
                             index=secid2fields[ticker]["date"][:len(secid2fields[ticker][mnemonic])]).astype(float)

        ts = pd.Series(secid2fields[ticker][mnemonic],index=secid2fields[ticker]["date"]).astype(float)
        return ts

    @staticmethod
    def get_secid2field(secids,secid_type, fields,start_date="", end_date="",overrides_dict={},req_type="histdata", api_host=None, return_ts=False):
        import time
        if api_host is None: api_host = bbgclient.get_next_available_host()
        if return_ts: fields = list(set(list(fields)+["date"]))
        url = "http://"+api_host+"/wic/api/v1.0/general_" + req_type + "?idtype="+secid_type+"&fields=" + ",".join([str(f) for f in fields]) + "&" + secid_type + "=" + ",".join([str(id) for id in secids]) + "&override=" + ",".join([str(k)+"hasvalue"+str(v) for (k,v) in overrides_dict.items()]) +"&start_date=" + start_date + "&end_date=" + end_date
        url = url.replace(" ","%20")

        secid2fields = {secid:{f:[] for f in fields} for secid in secids}
        try:
            with urllib.request.urlopen(url) as resp:
                html = resp.read().decode()

            parsed_json = json.loads(html)
            results = parsed_json[list(parsed_json.keys())[0]]
            for res in results:
                for key in res:
                    secid = key.split('/bbgid/')[1] if '/bbgid/' in key else key
                    # secid = key if secid_type == 'tickers' else key.split('/bbgid/')[1]
                    if secid not in secid2fields:
                        continue # error
                    bbgid_data = res[key]
                    for f in fields:
                        if f not in bbgid_data["fields"]:
                            secid2fields[secid][f].append(None)
                            continue
                        for fdata in bbgid_data["fields"][f]:
                            secid2fields[secid][f].append(fdata)
        except Exception as e:
            print('exception in bbgclient.get_secid2field for secids ' + ",".join(secids) + str(e.message))
        finally:
            if return_ts:
                return { secid: { fld: pd.Series(secid2fields[secid][fld],index=secid2fields[secid]["date"]).astype(float)
                            for fld in [f for f in fields if f.lower() != "date"]
                    } for secid in secids }

            return secid2fields

    # this function must first configure excel file in bloomberg_excel folder in the api server.
    # the excel file will contain a mnemonic that is only accessible through excel
    @staticmethod
    def get_physical_excel(full_filename, api_host='esansone-nb'):
        # currenly only esansone-nb supports excel file

        url = "http://"+api_host+"/wic/api/v1.0/excel?excel_filename="+full_filename
        url = url.replace(" ","%20")
        res = {"result":[], "status":[], "error": []}
        try:
            with urllib.request.urlopen(url) as resp:
                html = resp.read().decode()

            dict_result = json.loads(html)
            res = dict_result
        except Exception as e:
            res = {"result":[], "status":"error", "error": str(e.message)}
        finally:
            return res

    @staticmethod
    def refdata_api_result_to_df(bbg_api_res):
        if not isinstance(bbg_api_res, dict): raise Exception("invalid bloomberg api result")
        columns = ['Identifier']
        identifiers = bbg_api_res.keys()
        rows=[]
        for identifier in identifiers:
            fields = bbg_api_res[identifier]
            columns += fields
            vals = []
            for field in fields:
                if len(bbg_api_res[identifier][field]) == 1:
                    vals.append(bbg_api_res[identifier][field][0])


