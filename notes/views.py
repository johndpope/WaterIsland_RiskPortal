import datetime
from django.views.generic import ListView
from .models import NotesMaster, NotesAttachments
from django.http import HttpResponse, JsonResponse


# Create your views here.


class ListNotes(ListView):
    """ Render a Page with Latest News Items as List """
    model = NotesMaster
    template_name = 'wic_notes_list.html'


def get_attachments(request):
    """ Retreives the uploaded attachement for the Note """
    attachments = None
    if request.method == 'POST':
        notes_id = request.POST['notes_id']
        attachments = []
        for file in NotesAttachments.objects.filter(notes_id_id=notes_id):
            attachments.append({
                'filename':file.filename(),
                'url':file.notes_attachment.url
            })

    return JsonResponse({'attachments': attachments})


def create_note(request):
    """ Async. To add a new Notes Item """
    response = None

    if request.method == 'POST':
        try:
            author = request.POST['author']
            date = request.POST['date']
            title = request.POST['title']
            article = request.POST['article']
            tickers = request.POST['tickers']
            new_notes_item = NotesMaster.objects.create(author=author, date=date, title=title,
                                                        article=article, tickers=tickers)
            print('Now saving, File Uploads...')
            notes_fiies = request.FILES.getlist('filesNotes[]')

            if notes_fiies is not None:
                for file in notes_fiies:
                    NotesAttachments(notes_id_id=new_notes_item.id,
                                     uploaded_on=datetime.datetime.now().strftime('%Y-%m-%d'),
                                     notes_attachment=file).save()

            response = new_notes_item.id
        except Exception as e:
            print(e)
            response = 'failed'

    return HttpResponse(response)


def update_note(request):
    """ Async. Update News Item based on ID """
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
        print('Now saving, File Uploads...')
        notes_fiies = request.FILES.getlist('filesNotes[]')
        if notes_fiies is not None:
            for file in notes_fiies:
                NotesAttachments(notes_id_id=id,
                                 uploaded_on=datetime.datetime.now().strftime('%Y-%m-%d'),
                                 notes_attachment=file).save()
        response = id

    return HttpResponse(response)


def delete_note(request):
    response = None
    if request.method == 'POST':
        # Take the ID and Delete
        id_to_delete = request.POST['id']
        NotesMaster.objects.get(id=id_to_delete).delete()
        NotesAttachments.objects.filter(notes_id_id=id_to_delete).delete()
        response = 'wic_note_deleted'

    return HttpResponse(response)
