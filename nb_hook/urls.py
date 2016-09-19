from django.conf.urls import *
from . import views, views_v1

urlpatterns = [
    url(r'^$', views_v1.hook, name='hook'),

    url(r'^save_user/$', views.create_hook, name='save_user'),
    url(r'^save_update/$', views.update_hook, name='save_update'),
]
