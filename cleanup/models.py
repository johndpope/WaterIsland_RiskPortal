from django.db import models

# Create your models here.


class DeleteFile(models.Model):
    """
    Model to delete files from AWS S3.
    """
    file_details = models.FileField(null=True)
    aws_file_key = models.TextField(null=True)
    aws_bucket = models.CharField(max_length=63)
    requested_delete_at = models.DateField(null=True)
    deleted_from_aws_at = models.DateField(null=True)
