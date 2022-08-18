import json
from django.core.management.base import BaseCommand
from esr21_reports.views.graphs_mixins import (
    ScreeningGraphMixin,
    EnrollmentGraphMixin,
    VaccinationGraphMixin)
from esr21_reports.models import (
    AdverseEvents, ScreeningStatistics, EnrollmentStatistics,
    VaccinationStatistics, DashboardStatistics,
    VaccinationEnrollments, DemographicsStatistics)
from esr21_reports.views.enrollment_report_mixin import EnrollmentReportMixin
from esr21_reports.views.psrt_mixins import DemographicsMixin
from esr21_reports.views.psrt_mixins.summary_queries_mixin import PregnancySummaryMixin
from esr21_reports.views.adverse_events import (
    AdverseEventRecordViewMixin, SeriousAdverseEventRecordViewMixin)
from esr21_reports.views.psrt_mixins import ScreeningReportsViewMixin
from esr21_reports.views.site_helper_mixin import SiteHelperMixin
from esr21_reports.views import HomeView


class Command(BaseCommand):

    help = 'Populate reports forms'
    siteHelper = SiteHelperMixin()

    def handle(self, *args, **kwargs):
        self.populate_progress_reports()

    def populate_screening_data(self):
        screening = ScreeningGraphMixin()
        for site in self.siteHelper.sites_names:
            site_id = self.siteHelper.get_site_id(site)
            first_dose_screening = screening.first_dose_screening(site_id=site_id)
            second_dose_screening = screening.second_dose_screening(site_id=site_id)
            booster_dose_screening = screening.booster_dose_screening(site_id=site_id)
            ScreeningStatistics.objects.update_or_create(
                site=site,
                defaults={
                    'dose1': first_dose_screening,
                    'dose2': second_dose_screening,
                    'dose3': booster_dose_screening,
                }
            )
        screening_mixin = ScreeningReportsViewMixin()
        screening_statistics_json = json.dumps(screening_mixin.total_screened_participants)

        DashboardStatistics.objects.update_or_create(
            key='screening_statistics',
            value=screening_statistics_json
        )

    def populate_enrollement_data(self):
        enrollment = EnrollmentGraphMixin()
        for site in self.siteHelper.sites_names:
            site_id = self.siteHelper.get_site_id(site)
            male, female = enrollment.get_vaccinated_by_site(site_id)
            total = male + female
            defaults = {
                'total': total,
                'male': male,
                'female': female
            }
            EnrollmentStatistics.objects.update_or_create(
                site=site,
                defaults=defaults
            )

    def populate_enrollement_enrollement_with_conhorts(self):
        enrollment = EnrollmentReportMixin()
        enrolled_participants = enrollment.enrolled_participants
        enrolled_participants_json = json.dumps(enrolled_participants)
        DashboardStatistics.objects.update_or_create(
            key='enrolled_statistics',
            value=enrolled_participants_json
        )

    def populate_vaccinate(self):
        enrollment = EnrollmentReportMixin()
        vaccinated_participants = [
                enrollment.received_one_doses,
                enrollment.received_two_doses,
                enrollment.received_booster_doses,
                enrollment.screening_for_second_dose,
                enrollment.screening_for_booster_dose
        ]

        vaccinated_participants_json = json.dumps(vaccinated_participants)
        DashboardStatistics.objects.update_or_create(
            key='vaccinated_statistics',
            value=vaccinated_participants_json
        )

    def populate_demographics(self):
        demographics = DemographicsMixin()
        demographics_json = json.dumps(demographics.demographics_statistics)
        DashboardStatistics.objects.update_or_create(
            key='demographics_statistics',
            value=demographics_json
        )

    def populate_genaral_statistics(self):
        ae = AdverseEventRecordViewMixin()
        sae = SeriousAdverseEventRecordViewMixin()
        ae_json = json.dumps(ae.ae_statistics)
        sae_json = json.dumps(sae.sae_statistics)

        DashboardStatistics.objects.update_or_create(
            key='ae_statistics',
            value=ae_json
        )

        DashboardStatistics.objects.update_or_create(
            key='sae_statistics',
            value=sae_json
        )

    def populate_vaccination_data(self):
        vaccine = VaccinationGraphMixin()
        for site in self.siteHelper.sites_names:
            site_id = self.siteHelper.get_site_id(site)
            first_dose = vaccine.site_dose_vaccination(
                site_id=site_id, dose='first_dose')
            second_dose = vaccine.site_dose_vaccination(
                site_id=site_id, dose='second_dose')
            booster_dose = vaccine.site_dose_vaccination(
                site_id=site_id, dose='booster_dose')
            defaults = {
                'dose_1_percent': first_dose,
                'dose_2_percent': second_dose,
                'dose_3_percent': booster_dose,
                'overall_percent': vaccine.overal_site_dose_vaccination(
                    site_id=site_id)
            }

            VaccinationStatistics.objects.update_or_create(
                site=site,
                defaults=defaults
            )

    def populate_vaccine_enrollments(self):
        enrollment_report = EnrollmentReportMixin()
        second_dose = enrollment_report.second_dose_enrollments_elsewhere()
        booster_dose = enrollment_report.booster_enrollment_elsewhere()
        doses = [second_dose, booster_dose]
        for dose in doses:
            defaults = {
                'sinovac': dose[1],
                'pfizer': dose[2],
                'moderna': dose[3],
                'janssen': dose[4],
                'astrazeneca': dose[5]
            }
            VaccinationEnrollments.objects.update_or_create(
                variable=dose[0],
                defaults=defaults
            )

    def populate_pregnancy_statistics(self):
        preg_summary = PregnancySummaryMixin()
        preg_statistics_json = json.dumps(preg_summary.pregnancy_statistics)
        DashboardStatistics.objects.update_or_create(
                key='pregnancy_statistics',
                value=preg_statistics_json
        )

    def populate_progress_reports(self):
        progress_reports = HomeView()
        for site in self.siteHelper.sites_names:
            site_id = self.siteHelper.get_site_id(site)
            screenings = progress_reports.get_site_screening(site_id=site_id)
            homologous_enrollments = progress_reports.cohort_participants(site_id=site_id)
            heterologous_enrollments = progress_reports.cohort(site_id=site_id)

            screening_defaults = {
                'dose1':  screenings[0],
                'dose2':  screenings[1],
                'dose3':  screenings[2],
                'totals': screenings[3],
            }

            ScreeningStatistics.objects.update_or_create(
                site=site,
                defaults=screening_defaults
            )

            sub_cohort, main_cohort, totals = homologous_enrollments
            enrol_defaults = {
                    'site': site,
                    'series': 'homologous',
                    'main_cohort': main_cohort,
                    'sub_cohort': sub_cohort,
                    'total': totals
            }

            EnrollmentStatistics.objects.update_or_create(
                site_series=f'{site}_homologous',
                defaults=enrol_defaults
            )

            sub_cohort, main_cohort, totals = heterologous_enrollments
            enrol_defaults = {
                    'site': site,
                    'series': 'heterologous',
                    'main_cohort': main_cohort,
                    'sub_cohort': sub_cohort,
                    'total': totals
                }
            EnrollmentStatistics.objects.update_or_create(
                site_series=f'{site}_heterologous',
                defaults=enrol_defaults
            )

            first, second, booster, total = progress_reports.homologous_vaccinations(site_id)
            vacc_defaults = {
                'site': site,
                'dose_1': first,
                'dose_2': second,
                'dose_3': booster,
                'overall': total,
                'series': 'homologous'
            }
            VaccinationStatistics.objects.update_or_create(
                site_series=f'{site}_homologous',
                defaults=vacc_defaults
            )

            # adverse events
            homologous_list = progress_reports.vaccination_model_cls.objects.filter(
                received_dose_before='first_dose').values_list(
                    'subject_visit__subject_identifier', flat=True).distinct()

            adverse_events = progress_reports.site_adverse_events(
                subject_identifiers=homologous_list, site_id=site_id)
            adverse_defaults = {
                'ae': adverse_events[0],
                'serious_ae': adverse_events[1],
                'special_ae': adverse_events[2],
                'total': sum(adverse_events),
                'series': 'homologous',
                'site': site,
            }
            AdverseEvents.objects.update_or_create(
                site_series=f'{site}_homologous',
                defaults=adverse_defaults
            )

            adverse_events = progress_reports.site_adverse_events(
                subject_identifiers=progress_reports.heterologous_enrols, site_id=site_id)
            adverse_defaults = {
                'ae': adverse_events[0],
                'serious_ae': adverse_events[1],
                'special_ae': adverse_events[2],
                'total': sum(adverse_events),
                'series': 'heterologous',
                'site': site,
            }
            AdverseEvents.objects.update_or_create(
                site_series=f'{site}_heterologous',
                defaults=adverse_defaults
            )

            # demographics
            demographics = progress_reports.site_demographics(
                subject_identifiers=homologous_list, site_id=site_id)
            demographics_defaults = {
                'male': demographics[0],
                'female': demographics[1],
                'hiv_pos': demographics[2],
                'hiv_neg': demographics[3],
                'hiv_ind': demographics[4],
                'pos_preg': demographics[5],
                'pos_covid': demographics[6],
                'pos_diabetes': demographics[7],
                'series': 'homologous',
            }
            DemographicsStatistics.objects.update_or_create(
                site_series=f'{site}_homologous',
                defaults=demographics_defaults
            )
            
            demographics = progress_reports.site_demographics(
                subject_identifiers=progress_reports.heterologous_enrols, site_id=site_id)
            demographics_defaults = {
                'male': demographics[0],
                'female': demographics[1],
                'hiv_pos': demographics[2],
                'hiv_neg': demographics[3],
                'hiv_ind': demographics[4],
                'pos_preg': demographics[5],
                'pos_covid': demographics[6],
                'pos_diabetes': demographics[7],
                'series': 'heterologous',
            }
            DemographicsStatistics.objects.update_or_create(
                site_series=f'{site}_heterologous',
                defaults=demographics_defaults
            )
