from django.db import models

# Create your models here.
class NotesMaster(models.Model):
    ''' Model for Notes Items.'''
    date = models.DateField()
    title = models.CharField(max_length=1000)
    author = models.CharField(max_length=1000)
    article = models.TextField()
    tickers = models.CharField(max_length=1000)

    def __str__(self):
        return self.title+'_'+self.author