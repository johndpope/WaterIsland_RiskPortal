import os
import paramiko
import sys
from datetime import datetime

import pandas as pd
import pysftp
from celery import shared_task
from django.conf import settings
from django.core.files import File
from django.db import connection
from sqlalchemy import create_engine

from position_rec import tradar_utils
from position_rec.models import PositionRecAttachments


# Defines the name of the file for download / upload
SFTP_GS_HOST = settings.SFTP_GS_HOST 
GOLDMAN_SACHS_FILE_NAME = 'SRPB_197346_1200122789_DATA_Custody_Pos_285713_125308.xls'
GOLDMAN_SACHS_FILE_PATH = 'outgoing/' + GOLDMAN_SACHS_FILE_NAME


@shared_task
def fetch_position_rec_file_from_sftp():
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None
    received_new_file = False
    with pysftp.Connection(SFTP_GS_HOST, username=settings.SFTP_GS_USERNAME, password=settings.SFTP_GS_PASSWORD, cnopts=cnopts) as sftp:
        file_attrs = sftp.stat(GOLDMAN_SACHS_FILE_PATH)
        file_modified = file_attrs.st_mtime if file_attrs and file_attrs.st_mtime else None
        if file_modified and datetime.fromtimestamp(file_modified).date() == datetime.now().date():
            sftp.get(GOLDMAN_SACHS_FILE_PATH)
            received_new_file = True
    if received_new_file:
        file_path = os.path.join(os.getcwd(), GOLDMAN_SACHS_FILE_NAME)
        if os.path.isfile(file_path):
            position_rec_attachment = PositionRecAttachments()
            position_rec_attachment.uploaded_by = 'Portal'
            position_rec_attachment.original_filename = GOLDMAN_SACHS_FILE_NAME
            position_rec_attachment.description = 'Position Rec File for Goldman Sachs for ' + datetime.now().date().strftime('%B %d, %Y')
            open_file = open(file_path, 'rb')
            django_file = File(open_file)
            position_rec_attachment.position_rec_attachment.save(GOLDMAN_SACHS_FILE_NAME, django_file, save=True)
            os.remove(file_path)


def strip_leading_zeroes(row):
    try:
        return int(row.lstrip('0'))
    except:
        return row.lstrip('0')

def remove_us_from_ticker(row):
    try:
        if 'us' in row.lower():
            split_ticker = row.strip().split(" ")
            for item in split_ticker:
                if item.strip().lower() == 'us':
                    split_ticker.remove(item)
            row = ' '.join(i.strip() for i in split_ticker)
    except Exception as e:
        print(row)
    return row


def clean_field(row):
    value_split = row.strip().split(" ")
    return ' '.join(i.strip() for i in value_split if i != '')



def calculate_breaks():
    try:
        tradar_df = tradar_utils.tradar.get_position_rec()
        tradar_df['ticker'] = tradar_df['ticker'].apply(clean_field)
        tradar_df['ticker'] = tradar_df['ticker'].apply(remove_us_from_ticker)
        tradar_df['fund'] = tradar_df['fund'].apply(clean_field)

        account_fund_df = pd.read_sql('SELECT * FROM position_rec_accountfundpositionrec;', connection)
        account_fund_df = account_fund_df[account_fund_df['third_party'] == 'Goldman Sachs']
        account_fund_df['account_no'] = account_fund_df['account_no'].apply(strip_leading_zeroes)
        account_fund_df['fund'] = account_fund_df['fund'].apply(clean_field)

        max_date = PositionRecAttachments.objects.latest('uploaded_on').uploaded_on
        latest_file = None
        latest_file_list = PositionRecAttachments.objects.filter(uploaded_on=max_date)
        if latest_file_list.exists():
            latest_file = latest_file_list.first()
        if latest_file:
            file_df = pd.read_excel(latest_file.position_rec_attachment.url, skiprows=7, parse_cols="A:AW")
            file_df.dropna(subset=['Client ID'], inplace=True)
            file_df = file_df[['Account Mnemonic', 'Account Number', 'Product Type', 'Trade Date Quantity', 'Symbol']]
            file_df['Symbol'] = file_df['Symbol'].apply(clean_field)
            file_df['Symbol'] = file_df['Symbol'].apply(remove_us_from_ticker)
            file_df['Trade Date Quantity'] = file_df['Trade Date Quantity'].astype(int)

            file_forwards_df = pd.read_excel(latest_file.position_rec_attachment.url, skiprows=7, parse_cols="AY:CU")
            file_forwards_df.dropna(subset=['Client ID'], inplace=True)
            file_forwards_df = file_forwards_df[['Account Mnemonic', 'Account Number', 'Product Type',
                                                 'Trade Date Quantity', 'iso']]
            file_forwards_df['iso'] = file_forwards_df['iso'].apply(clean_field)
            file_forwards_df['Trade Date Quantity'] = file_forwards_df['Trade Date Quantity'].astype(int)
            file_forwards_df.rename(columns={'iso': 'Symbol'}, inplace=True)

            file_df = file_df.append(file_forwards_df)

            file_df_merge = pd.merge(file_df, account_fund_df, left_on=['Account Number'], right_on=['account_no'],
                                     how='left')
            file_df_merge = file_df_merge[file_df_merge['excluded'] == 'No']

            file_forwards_df_merge = pd.merge(file_forwards_df, account_fund_df, left_on=['Account Number'],
                                              right_on=['account_no'], how='left')
            file_forwards_df_merge = file_forwards_df_merge[file_forwards_df_merge['excluded'] == 'No']

            break_df1 = pd.merge(file_df_merge, tradar_df, left_on=['fund', 'Symbol'], right_on=['fund', 'ticker'], how='outer')
            break_df1['Break'] = check_break(break_df1)

            break_df1.drop(columns=['Account Mnemonic', 'Product Type', 'Account Number', 'id_x', 'id_y', 'mnemonic',
                                    'type', 'excluded', 'date_updated'], inplace=True)
            break_df1.rename(columns={'Trade Date Quantity': 'trade_date_quantity', 'Symbol': 'symbol', 'ticker': 'ticker',
                                      'NetPosition': 'tradar_quantity', 'Break': 'is_break'}, inplace=True)
            break_df1['comments'] = ''
            break_df1['is_resolved'] = ~break_df1['is_break']
            push_df = break_df1
            push_to_table(push_df)
    except PositionRecAttachments.DoesNotExist:
        print("No Position Rec Attachments found")
    except Exception as error:
        print(error)


def push_to_table(dataframe):
    engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD +
                           "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
    con = engine.connect()
    dataframe.to_sql(con=con, name='position_rec_positionrecbreak', schema=settings.CURRENT_DATABASE,
                     if_exists='append', chunksize=10000, index=False)
    con.close()


def check_break(data_frame):
    data_frame['Trade Date Quantity'] = data_frame['Trade Date Quantity'].fillna(0).astype(int)
    data_frame['NetPosition'] = data_frame['NetPosition'].fillna(0).astype(int)
    data_frame['Break'] = data_frame['Trade Date Quantity'] != data_frame['NetPosition']
    return data_frame['Break']
