import json
from django.core.management.base import BaseCommand
from esr21_reports.views.graphs_mixins import (
    AgeDistributionGraphMixin,
    ScreeningGraphMixin,
    EnrollmentGraphMixin,
    VaccinationGraphMixin)
from esr21_reports.models import (
    AgeStatistics, ScreeningStatistics, EnrollmentStatistics,
    VaccinationStatistics, DashboardStatistics, VaccinationEnrollments)
from esr21_reports.views.enrollment_report_mixin import EnrollmentReportMixin
from esr21_reports.views.psrt_mixins import DemographicsMixin
from esr21_reports.views.psrt_mixins.summary_queries_mixin import PregnancySummaryMixin
from esr21_reports.views.adverse_events import (
    AdverseEventRecordViewMixin, SeriousAdverseEventRecordViewMixin)
from esr21_reports.views.psrt_mixins import ScreeningReportsViewMixin, StatsPerWeekMixin
from esr21_reports.views.site_helper_mixin import SiteHelperMixin


class Command(BaseCommand):

    help = 'Populate reports forms'
    siteHelper = SiteHelperMixin()

    def handle(self, *args, **kwargs):
        DashboardStatistics.objects.all().delete()
        self.populate_age_graph()
        self.populate_screening_data()
        self.populate_enrollement_data()
        self.populate_vaccination_data()
        self.populate_enrollement_enrollement_with_conhorts()
        self.populate_vaccinate()
        self.populate_demographics()
        self.populate_genaral_statistics()
        self.populate_vaccine_enrollments()
        self.populate_pregnancy_statistics()

    def populate_age_graph(self):
        age_distribution = AgeDistributionGraphMixin()
        for site in self.siteHelper.sites_names:
            site_id = self.siteHelper.get_site_id(site)
            min, lowerquartile, median, upperquartile, max, site_outliers = age_distribution.get_distribution_site(site_id)
            defaults = {
                'min': min,
                'lowerquartile': lowerquartile,
                'median': median,
                'upperquartile': upperquartile,
                'max': max,
                }
            AgeStatistics.objects.update_or_create(
                site=site,
                defaults=defaults
            )

    def populate_screening_data(self):
        screening = ScreeningGraphMixin()
        for site in self.siteHelper.sites_names:
            site_id = self.siteHelper.get_site_id(site)
            passed, failed = screening.get_screened_by_site(site_id=site_id)
            ScreeningStatistics.objects.update_or_create(
                site=site,
                defaults={
                    'passed': passed,
                    'failed': failed
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

