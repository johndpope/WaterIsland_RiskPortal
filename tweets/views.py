from django.http import HttpResponse,JsonResponse
from .models import tweepy_object, Twitter_Actors
# Create your views here.





def get_latest_tweets(request):
    #Send a JSON Response from Latest Tweets

    tweet_response = []

    for name in Twitter_Actors.objects.all().values_list('twitter_handle',flat=True):
        tweet_dict = {}
        status_object = tweepy_object.api.user_timeline(screen_name=name, count=1)[0]
        text = status_object.text
        pic = status_object.author.profile_image_url
        screen_name = status_object.author.screen_name
        tweet_dict['pic'] = pic
        tweet_dict['text'] = text
        tweet_dict['screen_name'] = screen_name
        tweet_response.append(tweet_dict)

    return JsonResponse(tweet_response,safe=False)