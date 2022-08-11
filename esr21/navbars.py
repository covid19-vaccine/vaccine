from django.conf import settings
from edc_lab_dashboard.dashboard_urls import dashboard_urls as lab_dashboard_urls
from edc_navbar import NavbarItem, site_navbars, Navbar

esr21 = Navbar(name='esr21')

esr21.append_item(
    NavbarItem(
        name='eligible_subject',
        label='Subject Screening',
        fa_icon='fa-user-plus',
        url_name=settings.DASHBOARD_URL_NAMES.get('screening_listboard_url')))

esr21.append_item(
    NavbarItem(
        name='consented_subject',
        label='Subjects',
        fa_icon='far fa-user-circle',
        url_name=settings.DASHBOARD_URL_NAMES.get('subject_listboard_url')))


esr21.append_item(
    NavbarItem(
        name='esr21_follow',
        title='Follow',
        label=None,
        fa_icon='fa-phone',
        url_name=settings.DASHBOARD_URL_NAMES.get('esr21_follow_book_listboard_url')))


esr21.append_item(
    NavbarItem(
        name='esr21_reports',
        title='Reports',
        label=None,
        fa_icon='fa-file',
        url_name=settings.DASHBOARD_URL_NAMES.get('esr21_reports_home_url')))


esr21.append_item(
    NavbarItem(
        name='lab',
        label=None,
        fa_icon='fa-flask',
        url_name=lab_dashboard_urls.get('requisition_listboard_url')))

esr21.append_item(
    NavbarItem(
        name='export data',
        label=None,
        fa_icon='fa-download',
        url_name='esr21_export:home_url'))

esr21.append_item(
    NavbarItem(name='synchronization',
               label='Sync Data',
               fa_icon='fa-exchange',
               url_name='edc_sync:home_url'))

# protocol deviations and  note to file
esr21.append_item(
    NavbarItem(
        name='protocol_deviations',
        label='Protocol Deviations',
        fa_icon='far fa-user-circle',
        url_name=settings.DASHBOARD_URL_NAMES.get('protocol_deviations_listboard_url')))

esr21.append_item(
    NavbarItem(
        name='note_to_file',
        label='Note to file',
        fa_icon='far fa-user-circle',
        url_name=settings.DASHBOARD_URL_NAMES.get('note_to_file_listboard_url')))

site_navbars.register(esr21)
