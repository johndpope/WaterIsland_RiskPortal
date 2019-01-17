from . import views
from django.conf.urls import url
app_name = 'news'

urlpatterns = [
    url('get_top_news',views.get_top_news,name='get_top_news'),
    url('list_news_from_wic',views.ListNews.as_view(),name='list_news_from_wic'),
    url('add_new_wic_news_item',views.add_new_wic_news_item,name='add_new_wic_news_item'),
    url('delete_wic_news_item',views.delete_wic_news_item, name='delete_wic_news_item'),
    url('update_wic_news_item',views.update_wic_news_item, name='update_wic_news_item'),
    url('get_article_from_url',views.get_article_from_url, name='get_article_from_url'),

]
