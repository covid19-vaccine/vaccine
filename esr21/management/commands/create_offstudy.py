
from django.apps import apps as django_apps
from django.core.management.base import BaseCommand
from edc_base.utils import get_utcnow
from edc_constants.constants import NO

class Command(BaseCommand):

    help = 'Put participants off-study'

    subject_offstudy_model = 'esr21_prn.subjectoffstudy'
    onschedule_model = 'esr21_subject.onschedule'

    @property
    def subject_offstudy_cls(self):
        return django_apps.get_model(self.subject_offstudy_model)
    
    @property
    def onschedule_cls(self):
        return django_apps.get_model(self.onschedule_model)
    

    def handle(self, *args, **kwargs):
        
        
        onschedule_idx = self.onschedule_cls.objects.values_list(
                'subject_identifier', flat=True).distinct()
        
        print(onschedule_idx.count())
        
        for sid in onschedule_idx:
            obj_dict = {}
            try:
                self.subject_offstudy_cls.objects.get(
                    subject_identifier=sid)
            except self.subject_offstudy_cls.DoesNotExist:
                
                obj_dict.update(
                    completed_study=NO,
                    offstudy_date=get_utcnow().date(),
                    reason='sponsor_terminated',
                )
                
                subject_offstudy =  self.subject_offstudy_cls(subject_identifier=sid,**obj_dict)
                subject_offstudy.save()   
            else:
                pass
