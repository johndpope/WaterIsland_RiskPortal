import newspaper
import datetime
import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.views.generic import ListView
from newsapi import NewsApiClient

from .models import NewsMaster
from notes.views import get_cleaned_ticker_string

news_api_key = '9ff06fee3b654053b9396245ad9faabe'
#Initialize
newsapi = NewsApiClient(api_key=news_api_key)
def get_top_news(request):
    top_finance_headlines = newsapi.get_top_headlines(category='business', country='us')
    return JsonResponse(top_finance_headlines)


def get_article_from_url(request):
    response = ''
    if request.method == 'POST':
        #Get the URL
        url = request.POST['url']
        article = newspaper.Article(url)
        article.download()
        article.parse()
        text = article.text.replace('\n', ' ').replace('\r', '')
        authors = ','.join(list(article.authors))
        #Process Text with NLP
        article.nlp()
        nlp_summary = article.summary.replace('\n', ' ').replace('\r', '')
        response = {'text':text, 'nlp_summary':nlp_summary, 'authors':authors}

    return JsonResponse(response)



class ListNews(ListView):
    ''' Render a Page with Latest News Items as List'''
    model = NewsMaster
    template_name = 'wic_news_list.html'


def add_new_wic_news_item(request):
    ''' Async. To add a new News Item '''
    response = None

    if request.method == 'POST':
        #Only Process POST requests
        #Get all the Parameters
        try:
            author = request.POST['author']
            date = request.POST['date']
            title = request.POST['title']
            source = request.POST['source']
            url = request.POST['url']
            article = request.POST['article']
            selected_tickers = request.POST.get('tickers', "")
            other_tickers = request.POST.get('other_tickers', "")
            tickers = get_cleaned_ticker_string(selected_tickers, other_tickers)
            new_news_item = NewsMaster.objects.create(author=author, date=date, title=title, source=source, url=url,
                                                      article=article, tickers=tickers)
            response = new_news_item.id
        except Exception as e:
            print(e)
            response = 'failed'

    return HttpResponse(response)


def get_news_details(request):
    """ Retreives all the details for the requested News """
    if request.method == 'POST':
        news_id = request.POST.get('news_id')
        news_details = []
        if news_id:
            news_details = {}
            try:
                note = NewsMaster.objects.get(id=news_id)
                news_details['article'] = note.article
                news_details['id'] = note.id
                news_details['date'] = note.date
                news_details['title'] = note.title
                news_details['author'] = note.author
                news_details['tickers'] = note.tickers
                news_details['url'] = note.url
                news_details['source'] = note.source
            except NewsMaster.DoesNotExist:
                news_details = []

    return JsonResponse({'news_details': news_details})


def update_wic_news_item(request):
    ''' Async. Update News Item based on ID '''
    response = None

    if request.method == 'POST':
        # Only Process POST requests
        # Get all the Parameters
        id = request.POST['id']
        author = request.POST['author']
        date = request.POST['date']
        title = request.POST['title']
        source = request.POST['source']
        url = request.POST['url']
        article = request.POST['article']
        tickers = request.POST['tickers']
        tickers = get_cleaned_ticker_string("", tickers)
        NewsMaster.objects.filter(id=id).update(author=author, date=date, title=title, source=source, url=url,
                                                article=article, tickers=tickers)

        response = id

    return HttpResponse(response)


def delete_wic_news_item(request):
    response = None
    if request.method == 'POST':
        #Take the ID and Delete
        id_to_delete = request.POST['id']
        NewsMaster.objects.get(id=id_to_delete).delete()
        response = 'wic_news_deleted'

    return HttpResponse(response)


def export_wic_news(request):
    wic_news_export = pd.DataFrame.from_records(NewsMaster.objects.all().values())
    del wic_news_export['id']
    del wic_news_export['article']
    wic_news_export.columns = ["Author", "Date", "Source", "Tickers", "Title", "URL"]
    wic_news_export = wic_news_export[["Date", "Title", "URL", "Author", "Source", "Tickers"]]
    now = datetime.datetime.now().strftime('%Y-%m-%d')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=WIC_News_Repository_'+now+'.csv'
    wic_news_export.to_csv(path_or_buf=response, index=False)

    return response
