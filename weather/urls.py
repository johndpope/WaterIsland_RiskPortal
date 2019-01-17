from django.conf.urls import url
from . import views
urlpatterns = [
    url('get_nyc_weather/',views.get_nyc_weather,name='get_nyc_weather'),

]
