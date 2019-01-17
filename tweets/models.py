from django.db import models

# Create your models here.
import tweepy
from tweepy.auth import OAuthHandler
class Twitter():
    def __init__(self):
        print('Twitter Initialized')
        self.consumer_key = '9PS881x4gPZ0TAjlG0w8AWfBv'
        self.consumer_secret = 'm71RndpI1JD6PKxrmtRFpOUhOTsHAatpz9wtMMi6wEknfDza4u'
        self.access_token = '94296477-EuNwnHKG0wGPLYKleErUOrKWegTLj4dBBPYy9nRDs'
        self.access_token_secret = 'Y8qGGUktQE3JCVIGHtmN6M7b9f90zM1y1SrHXeNbAeWcC'
        self.auth = OAuthHandler(self.consumer_key,self.consumer_secret)
        self.auth.set_access_token(self.access_token,self.access_token_secret)
        self.api = tweepy.API(self.auth)

tweepy_object = Twitter()

class Twitter_Actors(models.Model):
    ''' Model for retrieving the Tweets for these Actors '''
    twitter_handle = models.CharField(max_length=100)