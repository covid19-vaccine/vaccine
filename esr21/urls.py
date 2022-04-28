"""esr21 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from django.views.generic.base import RedirectView
from edc_action_item.admin_site import edc_action_item_admin
from edc_data_manager.admin_site import edc_data_manager_admin
from edc_identifier.admin_site import edc_identifier_admin
from edc_lab.admin_site import edc_lab_admin
from edc_locator.admin_site import edc_locator_admin
from edc_metadata.admin_site import edc_metadata_admin
from edc_reference.admin_site import edc_reference_admin
from edc_registration.admin_site import edc_registration_admin

from edc_appointment.admin_site import edc_appointment_admin
from edc_calendar.admin_site import edc_calendar_admin
from edc_call_manager.admin_site import edc_call_manager_admin
from edc_senaite_interface.admin_site import edc_senaite_interface_admin
from edc_sync.admin_site import edc_sync_admin
from edc_sync_files.admin_site import edc_sync_files_admin
from edc_visit_schedule.admin_site import edc_visit_schedule_admin
from esr21_export.admin_site import esr21_export_admin
from esr21_follow.admin_site import esr21_follow_admin
from esr21_prn.admin_site import esr21_prn_admin
from esr21_subject.admin_site import esr21_subject_admin

from .views import HomeView, AdministrationView

urlpatterns = [
    path('accounts/', include('edc_base.auth.urls')),
    path('admin/', include('edc_base.auth.urls')),

    path('admin/', edc_appointment_admin.urls),
    path('admin/', edc_calendar_admin.urls),
    path('admin/', edc_lab_admin.urls),
    path('admin/', edc_data_manager_admin.urls),
    path('admin/', edc_data_manager_admin.urls),
    path('admin/', edc_locator_admin.urls),
    path('admin/', edc_action_item_admin.urls),
    path('admin/', edc_identifier_admin.urls),
    path('admin/', edc_metadata_admin.urls),
    path('admin/', edc_registration_admin.urls),
    path('admin/', edc_reference_admin.urls),
    path('admin/', edc_senaite_interface_admin.urls),
    path('admin/', edc_sync_admin.urls),
    path('admin/', edc_sync_files_admin.urls),

    path('admin/', esr21_follow_admin.urls),
    path('admin/', esr21_subject_admin.urls),
    path('admin/', esr21_prn_admin.urls),
    path('admin/', esr21_export_admin.urls),
    path('admin/', admin.site.urls),
    path('admin/edc_visit_schedule/', edc_visit_schedule_admin.urls),

    path('administration/', AdministrationView.as_view(),
         name='administration_url'),
    path('admin/esr21_subject/',
         RedirectView.as_view(url='admin/esr21_subject/'),
         name='esr21_subject_models_url'),
    path('admin/esr21_prn/',
         RedirectView.as_view(url='admin/esr21_prn/'),
         name='esr21_prn_models_url'),
    path('esr21_follow/', include('esr21_follow.urls')),

    path('edc_lab/', include('edc_lab.urls')),
    path('edc_lab_dashboard/', include('edc_lab_dashboard.urls')),
    path('edc_label/', include('edc_label.urls')),
    path('edc_sync_data_report/', include('edc_sync_data_report.urls')),

    path('edc_base/', include('edc_base.urls')),
    path('edc_consent/', include('edc_consent.urls')),
    path('esr21_subject/', include('esr21_subject.urls')),
    path('esr21_prn/', include('esr21_prn.urls')),
    path('esr21_export/', include('esr21_export.urls')),
    path('subject/', include('esr21_dashboard.urls')),
    path('edc_device/', include('edc_device.urls')),
    path('edc_protocol/', include('edc_protocol.urls')),
    path('edc_subject_dashboard/', include('edc_subject_dashboard.urls')),
    path('edc_visit_schedule/', include('edc_visit_schedule.urls')),
    path('edc_senaite_interface/', include('edc_senaite_interface.urls')),
    path('admin/edc_visit_schedule/', edc_visit_schedule_admin.urls),
    path('admin/edc_call_manager/', edc_call_manager_admin.urls),
    path('esr21_reports/', include('esr21_reports.urls')),

    path('edc_appointment/', include('edc_appointment.urls')),
    path('edc_action_item/', include('edc_action_item.urls')),
    path('edc_calendar/', include('edc_calendar.urls')),
    path('edc_data_manager/', include('edc_data_manager.urls')),
    path('edc_call_manager/', include('edc_call_manager.urls')),
    path('edc_reference/', include('edc_reference.urls')),
    path('edc_sync/', include('edc_sync.urls')),
    path('edc_sync_files/', include('edc_sync_files.urls')),

    path('subject/', include('esr21_dashboard.urls')),
    path('edc_meddra/', include('edc_meddra.urls')),

    path('switch_sites/', LogoutView.as_view(next_page=settings.INDEX_PAGE),
         name='switch_sites_url'),
    path('home/', HomeView.as_view(), name='home_url'),
    path('', HomeView.as_view(), name='home_url'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
