from django.apps import apps as django_apps
from django.conf import settings
from django.core.management.base import BaseCommand

from edc_senaite_interface.classes import AnalysisResult


class Command(BaseCommand):

    help = 'Populate covid 19 results form, (bhplims integration)'

    @property
    def subject_requisition_cls(self):
        return django_apps.get_model('esr21_subject.subjectrequisition')

    @property
    def covid19_results(self):
        return django_apps.get_model('esr21_subject.covid19results')

    @property
    def subject_visit(self):
        return django_apps.get_model('esr21_subject.subjectvisit')

    def handle(self, *args, **kwargs):
        analysis_result = AnalysisResult(host=settings.HOST)

        authenticated = analysis_result.auth(
            settings.SENAITE_USER, settings.SENAITE_PASS)

        results_created = 0
        results_updated = 0
        if authenticated:
            results = analysis_result.get_pcr_results()

            for result in results:
                try:
                    subject_visit = self.subject_visit.objects.get(
                        subject_identifier=result.get('subject_identifier'),
                        visit_code=result.get('visit_code'),
                        visit_code_sequence=result.get('visit_code_sequence'))
                except self.subject_visit.DoesNotExist:
                    pass
                else:
                    created, _ = self.covid19_results.objects.update_or_create(
                        subject_visit=subject_visit,
                        defaults={'covid_result': result.get('covid_result')})
                    if created:
                        results_created += 1
                    results_updated += 1
        self.stdout.write(self.style.SUCCESS(f'Results created: {results_created}.'))
        self.stdout.write(self.style.SUCCESS(f'Results updated: {results_updated}.'))
