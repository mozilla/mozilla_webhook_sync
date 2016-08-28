from django.conf.urls import *
from . import views

urlpatterns = [
    url(r'^$', views.hook, name='hook'),
    url(r'^update/$', views.update, name='update')
]
