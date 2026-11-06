from django.apps import apps as django_apps
from django.contrib import admin

for modelo in django_apps.get_app_config(__package__.split(".")[-1]).get_models():
    try:
        admin.site.register(modelo)
    except admin.sites.AlreadyRegistered:
        pass
