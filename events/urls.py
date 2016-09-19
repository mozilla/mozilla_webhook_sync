from django.conf.urls import *
from . import views

urlpatterns = [
    # url(r'^fetch_events/$', views.fetch_events, name='fetch_events'),
    url(r'^fetch/$', views.run)
]
