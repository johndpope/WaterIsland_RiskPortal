import datetime
import re

from django.conf import settings
from django.views.generic import ListView
from django.http import HttpResponse, JsonResponse

from cleanup.models import DeleteFile
from email_utilities import send_email
from notes.models import NotesMaster, NotesAttachments


class ListNotes(ListView):
    """ Render a Page with Latest News Items as List """
    model = NotesMaster
    template_name = 'wic_notes_list.html'
    queryset = NotesMaster.objects.all().order_by('-date')


def get_note_details(request):
    """ Retreives the uploaded attachement for the Note """
    attachments = None
    if request.method == 'POST':
        notes_id = request.POST['notes_id']
        attachments = []
        note_details = {}
        for file in NotesAttachments.objects.filter(notes_id_id=notes_id):
            attachments.append({
                'id': file.id,
                'notes_id': notes_id,
                'filename':file.filename(),
                'url':file.notes_attachment.url
            })
        try:
            note = NotesMaster.objects.get(id=notes_id)
            note_details['article'] = note.article
            note_details['id'] = note.id
            note_details['date'] = note.date
            note_details['title'] = note.title
            note_details['author'] = note.author
            note_details['tickers'] = note.tickers
        except NotesMaster.DoesNotExist:
            note_details = []

    return JsonResponse({'attachments': attachments, 'note_details': note_details})


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
            emails = request.POST.get('emails')
            emails = re.sub("[ ]", "", emails)
            emails = re.sub("[,:;]", ",", emails)
            email_list = emails.split(",")
            if email_list:
                email_list += ['vaggarwal@wicfunds.com', 'kgorde@wicfunds.com']
            file_urls = ""
            new_notes_item = NotesMaster.objects.create(author=author, date=date, title=title,
                                                        article=article, tickers=tickers)
            notes_fiies = request.FILES.getlist('filesNotes[]')

            if notes_fiies:
                for index, file in enumerate(notes_fiies):
                    uploaded_file = NotesAttachments.objects.create(notes_id_id=new_notes_item.id, original_filename=file.name,
                                                                    uploaded_on=datetime.datetime.now().strftime('%Y-%m-%d'),
                                                                    notes_attachment=file)
                    file_urls += "{index}) <a href='{url}' target='_blank'>{name}</a>".format(index=index+1,
                                    url=uploaded_file.notes_attachment.url, name=file.name)

            content = ""
            if title:
                content += "<p><strong>Title:</strong> {title}</p>".format(title=title)
            if author:
                content += "<p><strong>Author:</strong> {author}</p>".format(author=author)
            if tickers:
                content += "<p><strong>Tickers:</strong> {tickers}</p>".format(tickers=tickers)
            if article:
                content += "<p><strong>Article:</strong> {article}</p>".format(article=article)
            if file_urls:
                content += "<p><strong>Attachment URLs:</strong> {file_urls}</p>".format(file_urls=file_urls)

            subject = '(Risk Automation) Note Created for {tickers} ({date})'.format(tickers=tickers, date=date)
            html = """ \
                    <html>
                        <head>
                        </head>
                        <body>
                            {content}
                        </body>
                    </html>
                    """.format(content=content)
            send_email(from_addr=settings.EMAIL_HOST_USER, pswd=settings.EMAIL_HOST_PASSWORD,
                       recipients=email_list,
                       subject=subject, from_email='dispatch@wicfunds.com', html=html)
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
