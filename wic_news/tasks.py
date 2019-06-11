# coding: utf-8
import datetime
import io
import os
from celery import shared_task
import django
from django.conf import settings
import pandas as pd
from sqlalchemy import create_engine

from email_utilities import send_email

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WicPortal_Django.settings")
django.setup()


@shared_task
def email_news_additions():
    """ New News Articles Added Report. Runs from Mon-Fri at 7.15pm """
    try:
        engine = create_engine("mysql://" + settings.WICFUNDS_DATABASE_USER + ":" + settings.WICFUNDS_DATABASE_PASSWORD
                               + "@" + settings.WICFUNDS_DATABASE_HOST + "/" + settings.WICFUNDS_DATABASE_NAME)
        con = engine.connect()

        news_df = pd.read_sql_query(
            'SELECT * FROM ' + settings.CURRENT_DATABASE + '.wic_news_newsmaster where `date` = "' +
            datetime.datetime.now().date().strftime('%Y-%m-%d')+'"', con=con)

        del news_df['id']
        del news_df['article']
        news_df.rename(columns={'date': 'Date', 'title': 'Headline', 'source': 'Source', 'url': 'URL',
                                'author': 'Author', 'tickers': 'Tickers'} , inplace=True)

        news_attachment = news_df.copy()
        news_df['URL'] = news_df['URL'].apply(lambda x: '<a href="' + x + '">'+x+'</a>')
        print(news_df)
        total_articles_added = len(news_df)

        def export_excel(df):
            with io.BytesIO() as buffer:
                writer = pd.ExcelWriter(buffer)
                df.to_excel(writer)
                writer.save()
                return buffer.getvalue()

        news_df = news_df.style.set_table_styles([
            {'selector': 'tr:hover td', 'props': [('background-color', 'yellow')]},
            {'selector': 'th, td', 'props': [('border', '1px solid black'),
                                             ('padding', '4px'),
                                             ('text-align', 'center')]},
            {'selector': 'th', 'props': [('font-weight', 'bold')]},
            {'selector': '', 'props': [('border-collapse', 'collapse'),
                                       ('border', '1px solid black')]}
        ])

        html = """ \
                <html>
                  <head>
                  </head>
                  <body>
                    <p>Total News articles recorded today: {0}</p>
                    <a href="http://192.168.0.16:8000/news/list_news_from_wic">
                    Click to view News Repository..</a><br><br>
                    {1}
                  </body>
                </html>
        """.format(total_articles_added, news_df.hide_index().render(index=False))

        exporters = {'Situation Logs (' + datetime.datetime.now().date().strftime('%Y-%m-%d') + ').xlsx':
                         export_excel}

        subject = 'Situation Logs - ' + datetime.datetime.now().date().strftime('%Y-%m-%d')
        send_email(from_addr=settings.EMAIL_HOST_USER, pswd=settings.EMAIL_HOST_PASSWORD,
                   recipients=['kgorde@wicfunds.com', 'cwatkins@wicfunds.com', 'vaggarwal@wicfunds.com',
                               'kkeung@wicfunds.com', 'tchen@wicfunds.com', 'rlogan@wicfunds.com',
                               'bmoore@wicfunds.com', 'gloprete@wicfunds.com'],
                   subject=subject, from_email='dispatch@wicfunds.com', html=html,
                   EXPORTERS=exporters, dataframe=news_attachment
                   )

    except Exception as e:
        print('Error Occured....')
        print(e)


