from django.core.management.base import BaseCommand
from django.apps import apps as django_apps
from django.core.exceptions import ObjectDoesNotExist
from esr21_subject.helper_classes import EnrollmentHelper
from edc_visit_schedule.site_visit_schedules import site_visit_schedules

'''
Management command to switch participants between cohorts
1. check participant current schedule
2. enroll participant in a different schedule
3.
'''


class Command(BaseCommand):
    help = 'Switch participant between cohorts'
    schedule_enrollment = EnrollmentHelper

    def handle(self, *args, **kwargs):
        subject_identifier = kwargs.get('subject_identifier')
        schedule_name = self.get_current_cohort_enrolled(subject_identifier)
        self.enrol_subject(
            schedule_name=schedule_name,
            subject_identifier=subject_identifier)

    def add_arguments(self, parser):
        parser.add_argument(
            'subject_identifier', type=str,
            help='Subject identifier to switch cohort')

    # check the current participant enrolled cohort
    def get_current_cohort_enrolled(self, subject_identifier=None):
        if subject_identifier:
            onschedule = self.onschedule_cls.objects.filter(
                subject_identifier=subject_identifier).first()
            return onschedule.schedule_name

    @property
    def onschedule_cls(self):
        onschedule_model = 'esr21_subject.onschedule'
        return django_apps.get_model(onschedule_model)

    @property
    def subject_schedule_history_cls(self):
        subject_history_model = 'edc_visit_schedule.subjectschedulehistory'
        return django_apps.get_model(subject_history_model)

    @property
    def subject_visit_cls(self):
        maternalvisit_model = 'esr21_subject.subjectvisit'
        return django_apps.get_model(maternalvisit_model)

    @property
    def appointment_model_cls(self):
        appointment_model = 'edc_appointment.appointment'
        return django_apps.get_model(appointment_model)

    @property
    def subject_consent_cls(self):
        subject_consent_model = 'esr21_subject.informedconsent'
        return django_apps.get_model(subject_consent_model)

    def appointments(self, subject_identifier):
        """Returns a Queryset of all appointments for this subject.
        """
        if not self._appointments:
            self._appointments = self.appointment_model_cls.objects.filter(
                subject_identifier=subject_identifier).order_by(
                'visit_code')
        return self._appointments

    def get_onschedule_model_obj(self, schedule, subject_identifier):
        try:
            return schedule.onschedule_model_cls.objects.get(
                subject_identifier=subject_identifier,
                schedule_name=schedule.name)
        except ObjectDoesNotExist:
            return None

    def enrol_subject(self, schedule_name, subject_identifier=None):
        new_cohort = None
        # if the current cohort is sub cohort then new cohort is main cohort
        if 'sub' in schedule_name:
            new_cohort = 'esr21'
        else:
            new_cohort = 'esr21_sub'
        old_schedules = self.onschedule_cls.objects.filter(
                subject_identifier=subject_identifier).order_by('created')[:2]

        # check consent version date, if it is before v3 then enroll
        # into v1 schedule otherwise enroll into v3 schedule
        try:
            consent = self.subject_consent_cls.objects.get(
                subject_identifier=subject_identifier)
        except self.subject_consent_cls.DoesNotExist:
            pass
        else:
            '''
            TODO:
            consent_date = consent.consent_date
            check if consent date is less that 05/05/2022 last day of v1 consent
            enroll participant into schedule (v1 or v3) based on their consent date
            '''
            self.v1_schedule_enrollment(
                cohort=new_cohort, subject_identifier=subject_identifier)
            self.delete_old_appt(
                old_schedules=old_schedules,
                subject_identifier=subject_identifier,
                new_cohort=new_cohort)

    def v1_schedule_enrollment(self, cohort, subject_identifier):
        onschedule_model = 'esr21_subject.onschedule'
        try:
            screening_eligibility = self.screening_eligibility_cls.objects.get(
                subject_identifier=subject_identifier)
        except ObjectDoesNotExist:
            pass
        else:
            if screening_eligibility.is_eligible:
                self.put_on_schedule(
                    f'{cohort}_enrol_schedule',
                    onschedule_model=onschedule_model,
                    onschedule_datetime=screening_eligibility.created.replace(
                        microsecond=0),
                    subject_identifier=subject_identifier)

                self.put_on_schedule(
                    f'{cohort}_fu_schedule',
                    onschedule_model=onschedule_model,
                    onschedule_datetime=screening_eligibility.created.replace(
                        microsecond=0),
                    subject_identifier=subject_identifier)

    def v3_schedule_enrollment(self, cohort, subject_identifier):
        schedule_enrollment = self.schedule_enrollment(
            cohort=cohort, subject_identifier=subject_identifier)
        schedule_enrollment.schedule_enrol()

    def put_on_schedule(self, schedule_name, onschedule_model,
                        onschedule_datetime=None, subject_identifier=None):
        _, schedule = site_visit_schedules.get_by_onschedule_model_schedule_name(
            onschedule_model=onschedule_model, name=schedule_name)
        schedule.put_on_schedule(
            subject_identifier=subject_identifier,
            onschedule_datetime=onschedule_datetime,
            schedule_name=schedule_name)

    @property
    def vaccination_history_model_cls(self):
        return django_apps.get_model(self.vaccination_history_model)

    @property
    def screening_eligibility_cls(self):
        screening_eligibility_model = 'esr21_subject.screeningeligibility'
        return django_apps.get_model(screening_eligibility_model)

    def delete_old_appt(self,
                        old_schedules=None,
                        subject_identifier=None,
                        new_cohort=None):

        new_schedules = [
            f'{new_cohort}_enrol_schedule',
            f'{new_cohort}_fu_schedule',
        ]
        for onschedule in old_schedules:
            old_appts = self.appointment_model_cls.objects.filter(
                subject_identifier=subject_identifier,
                schedule_name=onschedule.schedule_name)
            for appt in old_appts:
                try:
                    g = self.appointment_model_cls.objects.get(
                        subject_identifier=appt.subject_identifier,
                        visit_code=appt.visit_code,
                        schedule_name__in=new_schedules)
                    g.appt_status = appt.appt_status
                    g.appt_datetime = appt.appt_datetime
                    g.appt_reason = appt.appt_reason
                    g.comment = appt.comment
                    g.save()
                except self.appointment_model_cls.DoesNotExist:
                    pass
                else:
                    try:
                        mm = self.subject_visit_cls.objects.get(
                            appointment=appt)
                    except self.subject_visit_cls.DoesNotExist:
                        pass
                    else:
                        mm.appointment = g
                        mm.save_base(raw=True)
                try:
                    history_obj = self.subject_schedule_history_cls.objects.get(
                        subject_identifier=appt.subject_identifier,
                        schedule_name=appt.schedule_name
                    )
                except self.subject_schedule_history_cls.DoesNotExist:
                    pass
                else:
                    history_obj.delete()
                appt.delete()
            onschedule.delete()
