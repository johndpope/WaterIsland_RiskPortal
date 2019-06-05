import os
import uuid

from django.db import models


EXCLUDED_CHOICES = (
    ('No', 'No'),
    ('Yes', 'Yes'),
)


class AccountFundPositionRec(models.Model):
    """
    Models for Account Fund Mapping for Position Reconciliation
    """
    third_party = models.CharField(null=True, blank=True, max_length=100)
    account_no = models.CharField(null=True, blank=True, max_length=10)
    mnemonic = models.CharField(null=True, blank=True, max_length=10)
    type = models.CharField(null=True, blank=True, max_length=100)
    fund = models.CharField(null=True, blank=True, max_length=10)
    excluded = models.CharField(null=True, blank=True, max_length=100, choices=EXCLUDED_CHOICES)
    date_updated = models.DateTimeField(null=False)


def get_position_rec_path_filename(instance, filename):
    path = 'POSITION_REC_ATTACHMENTS'
    file_split = filename.split('.')
    ext = file_split[-1]
    filename = file_split[0]
    filename = '{filename}_{uuid}.{ext}'.format(filename=filename, uuid=str(uuid.uuid4()), ext=ext)
    return os.path.join(path, filename)

class PositionRecAttachments(models.Model):
    """ Model for Position Rec Files Attachments."""
    position_rec_attachment = models.FileField(null=True, upload_to=get_position_rec_path_filename)
    original_filename = models.CharField(default='filename', max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    uploaded_by = models.CharField(max_length=100, null=True)
    uploaded_on = models.DateField(auto_now_add=True)

    def filename(self):
        return self.original_filename


class PositionRecBreak(models.Model):
    third_party = models.CharField(max_length=255, null=True, blank=True)
    fund = models.CharField(max_length=100, null=True, blank=True)
    ticker = models.CharField(max_length=255, null=True, blank=True)
    symbol = models.CharField(max_length=255, null=True, blank=True)
    tradar_quantity = models.IntegerField(default=0)
    trade_date_quantity = models.IntegerField(default=0)
    account_no = models.CharField(max_length=255)
    comments = models.CharField(max_length=255, null=True, blank=True)
    is_resolved = models.BooleanField()
    is_break = models.BooleanField()
    number_of_days = models.IntegerField(default=0)
