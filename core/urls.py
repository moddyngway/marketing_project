from django.contrib import admin
from django.urls import path
import core.views as core_views


urlpatterns = [
    path("", core_views.HomeView.as_view(), name="home"),
    path('bearbeitungsdaten/<int:kunde_nr>/', core_views.BearbeitungsdatenView.as_view(), name='bearbeitungsdaten'),
    path('new_customer/', core_views.NewCustomerView.as_view(), name='new_customer'),
]