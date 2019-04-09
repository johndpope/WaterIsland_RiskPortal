import os
import uuid
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


def get_notes_path_filename(instance, filename):
    path = 'NOTES_ATTACHMENTS'
    file_split = filename.split('.')
    ext = file_split[-1]
    filename = file_split[0]
    filename = '{filename}_{uuid}.{ext}'.format(filename=filename, uuid=str(uuid.uuid4()), ext=ext)
    return os.path.join(path, filename)

class NotesAttachments(models.Model):
    """ Model for Notes Files Attachments."""
    notes_id = models.ForeignKey('NotesMaster', on_delete=models.CASCADE)
    notes_attachment = models.FileField(null=True, upload_to=get_notes_path_filename)
    original_filename = models.CharField(default='filename', max_length=100)
    uploaded_on = models.DateField(null=True)

    def filename(self):
        return self.original_filename
