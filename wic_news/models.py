from django.db import models

# Create your models here.
class NewsMaster(models.Model):
    ''' Model for News Items.'''
    date = models.DateField()
    title = models.CharField(max_length=1000)
    source = models.CharField(max_length=1000)
    url = models.URLField()
    author = models.CharField(max_length=1000)
    article = models.TextField()
    tickers = models.CharField(max_length=1000)

    def __str__(self):
        return self.title+'_'+self.source