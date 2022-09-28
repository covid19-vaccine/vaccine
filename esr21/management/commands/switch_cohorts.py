'''
Management command to switch participants between cohorts
1. check participant current schedule
2. enroll participant in a different schedule
3.
'''

from django.apps import apps as django_apps
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.management.base import BaseCommand
from edc_base.utils import get_utcnow

from edc_appointment.constants import NEW_APPT
from edc_appointment.creators import AppointmentInProgressError
from edc_appointment.creators import InvalidParentAppointmentMissingVisitError
from edc_appointment.creators import InvalidParentAppointmentStatusError
from edc_appointment.creators import UnscheduledAppointmentCreator
from edc_appointment.creators import UnscheduledAppointmentError
from edc_visit_schedule.site_visit_schedules import site_visit_schedules
from esr21_subject.helper_classes import EnrollmentHelper


class Command(BaseCommand):
    help = 'Switch participant between cohorts'
    schedule_enrollment = EnrollmentHelper

    def handle(self, *args, **kwargs):
        subject_identifier = kwargs.get('subject_identifier')
        # subject_identifier = kwargs.get('schedule_name')
        schedule_name = self.get_current_cohort_enrolled(subject_identifier)

        self.enrol_subject(
            old_schedule_name=schedule_name,
            subject_identifier=subject_identifier)

    def add_arguments(self, parser):
        parser.add_argument(
            'subject_identifier', type=str,
            help='Subject identifier to switch cohort')

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

    @property
    def vaccination_history_model_cls(self):
        return django_apps.get_model(self.vaccination_history_model)

    @property
    def screening_eligibility_cls(self):
        screening_eligibility_model = 'esr21_subject.screeningeligibility'
        return django_apps.get_model(screening_eligibility_model)

    # check the current participant enrolled cohort
    def get_current_cohort_enrolled(self, subject_identifier=None):
        if subject_identifier:
            onschedule = self.onschedule_cls.objects.filter(
                subject_identifier=subject_identifier).first()
            return onschedule.schedule_name

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

    def rename_old_appt(self, schedule_name=None, subject_identifier=None):

        old_appts = self.appointment_model_cls.objects.filter(
            subject_identifier=subject_identifier,
            schedule_name=schedule_name)

        for appt in old_appts:
            appt.schedule_name = appt.schedule_name + 'x'
            appt.save()

    def delete_old_appt(self, old_schedules=None, subject_identifier=None, new_cohort=None):

        new_schedules = [
            f'{new_cohort}_enrol_schedule',
            f'{new_cohort}_fu_schedule',
        ]
        for onschedule in old_schedules:

            old_appts = self.appointment_model_cls.objects.filter(
                subject_identifier=subject_identifier,
                schedule_name__startswith=onschedule.schedule_name)

            for appt in old_appts:
                print(">>>>>>>>>>>>>", appt.visit_code)
                try:
                    g = self.appointment_model_cls.objects.get(
                        subject_identifier=appt.subject_identifier,
                        visit_code=appt.visit_code,
                        schedule_name__in=new_schedules)
                except self.appointment_model_cls.DoesNotExist:
                    unscheduled_appointment_cls = UnscheduledAppointmentCreator

                    prev_visit = None
                    prev_appt = appt

                    while not prev_visit:

                        prev_appt = prev_appt.previous_by_timepoint

                        try:
                            prev_visit = prev_appt.subjectvisit
                        except:
                            pass

                    if prev_visit and prev_appt:

                        options = {
                            'subject_identifier': appt.subject_identifier,
                            'visit_schedule_name': prev_appt.visit_schedule.name,
                            'schedule_name': prev_appt.schedule.name,
                            'visit_code': prev_appt.visit_code,
                            'suggested_datetime': get_utcnow(),
                            'check_appointment': False,
                            'appt_status': NEW_APPT,
                            'facility': prev_appt.facility
                        }

                        try:
                            unsc = unscheduled_appointment_cls(**options)
                        except (ObjectDoesNotExist, UnscheduledAppointmentError,
                                InvalidParentAppointmentMissingVisitError,
                                InvalidParentAppointmentStatusError,
                                AppointmentInProgressError) as e:
                            raise ValidationError(str(e))
                        else:

                            unsc_ap = unsc.appointment

                            try:
                                visit_obj = self.subject_visit_cls.objects.get(
                                    appointment=appt)
                            except self.subject_visit_cls.DoesNotExist:
                                pass
                            else:
                                visit_obj.appointment = unsc_ap
                                visit_obj.save()

                            unsc_ap.appt_status = appt.appt_status
                            unsc_ap.appt_datetime = appt.appt_datetime
                            unsc_ap.appt_reason = 'Unscheduled'
                            unsc_ap.comment = appt.comment
                            unsc_ap.save()
                    else:
                        print("whet????????", appt.visit_code)
                else:

                    try:
                        visit_obj = self.subject_visit_cls.objects.get(
                            appointment=appt)
                    except self.subject_visit_cls.DoesNotExist:
                        pass
                    else:
                        visit_obj.appointment = g
                        visit_obj.save()

                    g.appt_status = appt.appt_status
                    g.appt_datetime = appt.appt_datetime
                    g.appt_reason = appt.appt_reason
                    g.comment = appt.comment
                    g.save()

                try:
                    appt.delete()
                except:
                    print(appt.subject_identifier, appt.visit_code)
            onschedule.delete()

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

    def v1_schedule_enrollment(self, new_cohort, old_cohort, subject_identifier):

        onschedule_model = 'esr21_subject.onschedule'
        try:
            screening_eligibility = self.screening_eligibility_cls.objects.get(
                subject_identifier=subject_identifier)
        except ObjectDoesNotExist:
            pass
        else:
            if screening_eligibility.is_eligible:

                old_enrol_schedule_name = f'{old_cohort}_enrol_schedule'

                self.rename_old_appt(old_enrol_schedule_name, subject_identifier)

                # delete history objects
                self.subject_schedule_history_cls.objects.filter(
                    subject_identifier=subject_identifier,
                    schedule_name=old_enrol_schedule_name).delete()

                self.put_on_schedule(
                    f'{new_cohort}_enrol_schedule',
                    onschedule_model=onschedule_model,
                    onschedule_datetime=screening_eligibility.created.replace(
                        microsecond=0),
                    subject_identifier=subject_identifier)

                fu_schedule_name = f'{old_cohort}_fu_schedule'

                self.rename_old_appt(fu_schedule_name, subject_identifier)

                self.put_on_schedule(
                    f'{new_cohort}_fu_schedule',
                    onschedule_model=onschedule_model,
                    onschedule_datetime=screening_eligibility.created.replace(
                        microsecond=0),
                    subject_identifier=subject_identifier)

                old_schedules = self.onschedule_cls.objects.filter(
                    subject_identifier=subject_identifier,
                    schedule_name__startswith=old_cohort).exclude(
                        schedule_name__contains='boost')

                self.delete_old_appt(
                    old_schedules=old_schedules,
                    subject_identifier=subject_identifier,
                    new_cohort=new_cohort)

    def enrol_subject(self, old_schedule_name, subject_identifier=None):

        new_cohort = 'esr21_sub'
        old_cohort = 'esr21'

        # if the current cohort is sub cohort then new cohort is main cohort
        if 'sub' in old_schedule_name:
            new_cohort = 'esr21'
            old_cohort = 'esr21_sub'

        consents = self.subject_consent_cls.objects.filter(
            subject_identifier=subject_identifier)

        if consents:
            '''
            TODO:
            consent_date = consent.consent_date
            check if consent date is less that 05/05/2022 last day of v1 consent
            enroll participant into schedule (v1 or v3) based on their consent date
            '''
            self.v1_schedule_enrollment(
                new_cohort, old_cohort, subject_identifier=subject_identifier)
