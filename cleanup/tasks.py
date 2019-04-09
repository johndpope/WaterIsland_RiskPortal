from datetime import datetime

import boto3
from boto3.exceptions import botocore
from celery import shared_task
from django.conf import settings

from cleanup.models import DeleteFile
from email_utilities import send_email


@shared_task
def clean_up_aws_s3():
    """
    Delete files from AWS S3 storage
    """
    content = ""
    subject = 'AWS S3 File Clean Up - ' + datetime.now().date().strftime('%Y-%m-%d')
    try:
        client = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        files_to_be_deleted = DeleteFile.objects.filter(deleted_from_aws_at__isnull=True)
        if files_to_be_deleted:
            total_files_to_be_deleted = len(files_to_be_deleted)
            file_deleted_count = 0
            for file_details in files_to_be_deleted:
                response = client.delete_object(Bucket=file_details.aws_bucket, Key=file_details.aws_file_key)
                if response.get('DeleteMarker'):
                    file_deleted_count += 1
                    content += "<p>" + str(file_deleted_count) + ".) " + str(file_details.aws_file_key) + "</p>"
                    file_details.deleted_from_aws_at = datetime.now()
                    file_details.save()
                else:
                    content += '<p><font color="red">Could not delete file {file}</font></p>'.format(file=file_details.aws_file_key)
            content += "<p>{0} files deleted out of {1} files.</p>".format(str(file_deleted_count), str(total_files_to_be_deleted))
        else:
            content += "<p>No files to delete. AWS S3 is already cleaned-up.</p>"
    except botocore.client.ClientError as error:
        content += "<p><font color='red'>Client Error</p><p>{error}</font></p>".format(error=error)
    except Exception as error:
        content += "<p><font color='red'>ERROR</p><p>{error}</font></p>".format(error=error)
    html = """ \
            <html>
                <head>
                </head>
                <body>
                    <p>Following files were deleted from AWS S3 bucket:</p>
                    {content}
                </body>
            </html>
        """.format(content=content)
    send_email(from_addr=settings.EMAIL_HOST_USER, pswd=settings.EMAIL_HOST_PASSWORD,
               recipients=['vaggarwal@wicfunds.com', 'kgorde@wicfunds.com'],
               subject=subject, from_email='dispatch@wicfunds.com', html=html)
