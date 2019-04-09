import datetime

from django.views.generic import ListView
from django.http import HttpResponse, JsonResponse

from cleanup.models import DeleteFile
from notes.models import NotesMaster, NotesAttachments


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
                'id': file.id,
                'notes_id': notes_id,
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

            if notes_fiies:
                print(notes_fiies)
                for file in notes_fiies:
                    NotesAttachments(notes_id_id=new_notes_item.id, original_filename=file.name,
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
        remove_file_ids = request.POST.get('remove_file_ids')
        try:
            if remove_file_ids:
                remove_file_ids = remove_file_ids.split(",")
                notes_files = NotesAttachments.objects.filter(notes_id_id=id, id__in=remove_file_ids)
                for notes_file in notes_files:
                    notes_filefield = notes_file.notes_attachment
                    DeleteFile(file_details=notes_filefield,
                               aws_file_key=notes_filefield.file.obj.key,
                               aws_bucket=notes_filefield.file.obj.bucket_name,
                               requested_delete_at=datetime.datetime.now()).save()
                notes_files.delete()
                print('Deleted files', remove_file_ids)
        except Exception as error:
            print('Error Deleting files. File IDs are: ', remove_file_ids, error)
        NotesMaster.objects.filter(id=id).update(author=author, date=date, title=title,
                                                 article=article, tickers=tickers)
        print('Now saving, File Uploads...')
        notes_fiies = request.FILES.getlist('filesNotes[]')
        if notes_fiies:
            print(notes_fiies)
            for file in notes_fiies:
                NotesAttachments(notes_id_id=id, original_filename=file.name,
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
