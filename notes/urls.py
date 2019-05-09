from django.conf.urls import url
from . import views

app_name = 'notes'

urlpatterns = [
    url('create_note/', views.create_note, name='create_note'),
    url('update_note/', views.update_note, name='update_note'),
    url('delete_note/', views.delete_note, name='delete_note'),
    url('list_notes/', views.ListNotes.as_view(), name='list_notes'),
    url('get_note_details/', views.get_note_details, name='get_note_details'),
    url('search/', views.autocompleteModel, name='autocompleteModel')
]
