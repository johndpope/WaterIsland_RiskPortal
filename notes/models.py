import os
from django.db import models

# Create your models here.


class NotesMaster(models.Model):
    """ Model for Notes Items."""
    date = models.DateField()
    title = models.CharField(max_length=1000)
    author = models.CharField(max_length=1000)
    article = models.TextField()
    tickers = models.CharField(max_length=1000)

    def __str__(self):
        return self.title+'_'+self.author


class NotesAttachments(models.Model):
    """ Model for Notes Files Attachments."""
    notes_id = models.ForeignKey('NotesMaster', on_delete=models.CASCADE)
    notes_attachment = models.FileField(null=True, upload_to='NOTES_ATTACHMENTS')
    uploaded_on = models.DateField(null=True)

    def filename(self):
        return os.path.basename(self.notes_attachment.name)
