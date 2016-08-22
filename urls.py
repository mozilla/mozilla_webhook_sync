from django.contrib import admin
from django.conf import settings
from django.views.generic import TemplateView, RedirectView
from django.conf.urls import *

urlpatterns = [
    url('^hook/', include('nb_hook.urls'))
]