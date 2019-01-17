from django.db import models
from django.conf import settings
# Create your models here.
import tweepy
from tweepy.auth import OAuthHandler
class Twitter():
    def __init__(self):
        print('Twitter Initialized')
        self.consumer_key = settings.TWEEPY_CONSUMER_KEY
        self.consumer_secret = settings.TWEEPY_CONSUMER_KEY
        self.access_token = settings.TWEEPY_ACCESS_TOKEN
        self.access_token_secret = settings.TWEEPY_ACCESS_TOKEN_SECRET
        self.auth = OAuthHandler(self.consumer_key,self.consumer_secret)
        self.auth.set_access_token(self.access_token,self.access_token_secret)
        self.api = tweepy.API(self.auth)

tweepy_object = Twitter()

class Twitter_Actors(models.Model):
    ''' Model for retrieving the Tweets for these Actors '''
    twitter_handle = models.CharField(max_length=100)