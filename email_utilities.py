from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import smtplib
import io
import pandas as pd


def export_excel(df):
            with io.BytesIO() as buffer:
                writer = pd.ExcelWriter(buffer)
                df.to_excel(writer)
                writer.save()
                return buffer.getvalue()

def send_email(from_addr, pswd, recipients, subject, from_email, html='', EXPORTERS=[], dataframe=None):
    from_addr = from_addr
    login = from_addr
    pswd = pswd
    recipients = recipients
    emaillist = [elem.strip().split(',') for elem in recipients]
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = ', '.join(recipients)
    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    for filename in EXPORTERS:
        attachment = MIMEApplication(EXPORTERS[filename](dataframe))
        attachment['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        msg.attach(attachment)

    server = smtplib.SMTP('smtp.office365.com', 587)
    server.ehlo()
    server.starttls()
    server.login(login, pswd)
    server.sendmail(msg['From'], emaillist, msg.as_string())
