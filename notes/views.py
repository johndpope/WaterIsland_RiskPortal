from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import NotesMaster
from django.http import HttpResponse
# Create your views here.


class ListNotes(ListView):
    ''' Render a Page with Latest News Items as List'''
    model = NotesMaster
    template_name = 'wic_notes_list.html'


def create_note(request):
    ''' Async. To add a new Notes Item '''
    response = None

    if request.method == 'POST':
        #Only Process POST requests
        #Get all the Parameters
        try:
            author = request.POST['author']
            date = request.POST['date']
            title = request.POST['title']
            article = request.POST['article']
            tickers = request.POST['tickers']
            new_notes_item = NotesMaster.objects.create(author=author, date=date,title=title,article=article,tickers=tickers)
            response = new_notes_item.id
        except Exception as e:
            #print(e)
            response = 'failed'

    return HttpResponse(response)


def update_note(request):
    ''' Async. Update News Item based on ID '''
    response = None

    if request.method == 'POST':
        # Only Process POST requests
        # Get all the Parameters
        id = request.POST['id']
        author = request.POST['author']
        date = request.POST['date']
        title = request.POST['title']
        article = request.POST['article']
        tickers = request.POST['tickers']
        NotesMaster.objects.filter(id=id).update(author=author, date=date, title=title,
                                                  article=article, tickers=tickers)

        response = id

    return HttpResponse(response)


def delete_note(request):
    response = None
    if request.method == 'POST':
        #Take the ID and Delete
        id_to_delete = request.POST['id']
        NotesMaster.objects.get(id=id_to_delete).delete()
        response = 'wic_note_deleted'

    return HttpResponse(response)