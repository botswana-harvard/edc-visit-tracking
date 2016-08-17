from collections import OrderedDict

from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured

# from edc_export.actions import export_as_csv_action

from .models import CaretakerFieldsMixin


class CrfAdminMixin(object):

    """ModelAdmin subclass for models with a ForeignKey to your visit model(s)"""

    visit_model = None
    visit_attr = None
    date_hierarchy = 'report_datetime'

    def __init__(self, *args, **kwargs):
        super(CrfAdminMixin, self).__init__(*args, **kwargs)
        if not self.visit_model:
            raise ImproperlyConfigured('Class attribute \'visit model\' on BaseVisitModelAdmin '
                                       'for model {0} may not be None. Please correct.'.format(self.model))
        if not self.visit_attr:
            raise ValueError(
                'The admin class for \'{0}\' needs to know the field attribute that points to \'{1}\'. '
                'Specify this on the ModelAdmin class as \'visit_attr\'.'.format(
                    self.model._meta.model._meta.verbose_name, self.visit_model._meta.verbose_name))
        self.list_display = list(self.list_display)
        self.list_display.append(self.visit_attr)
        self.list_display = tuple(self.list_display)
        self.extend_search_fields()
        self.extend_list_filter()

    def extend_search_fields(self):
        self.search_fields = list(self.search_fields)
        self.search_fields.extend([
            '{}__appointment__subject_identifier'.format(self.visit_attr)])
        self.search_fields = tuple(set(self.search_fields))

    def extend_list_filter(self):
        """Extends list filter with additional values from the visit model."""
        self.list_filter = list(self.list_filter)
        self.list_filter.extend([
            self.visit_attr + '__report_datetime',
            self.visit_attr + '__reason',
            self.visit_attr + '__appointment__appt_status',
            self.visit_attr + '__appointment__visit_code',])
        self.list_filter = tuple(self.list_filter)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == self.visit_attr:
            if request.GET.get(self.visit_attr):
                kwargs["queryset"] = self.visit_model.objects.filter(id__exact=request.GET.get(self.visit_attr, 0))
            else:
                self.readonly_fields = list(self.readonly_fields)
                try:
                    self.readonly_fields.index(self.visit_attr)
                except ValueError:
                    self.readonly_fields.append(self.visit_attr)
        return super(CrfAdminMixin, self).formfield_for_foreignkey(db_field, request, **kwargs)

#     def get_actions(self, request):
#         actions = super(CrfAdminMixin, self).get_actions(request)
#         actions['export_as_csv_action'] = (
#             export_as_csv_action(
#                 exclude=['id', self.visit_attr],
#                 extra_fields=OrderedDict(
#                     {'subject_identifier':
#                      '{}__appointment__registered_subject__subject_identifier'.format(self.visit_attr),
#                      'visit_report_datetime': '{}__report_datetime'.format(self.visit_attr),
#                      'gender': '{}__appointment__registered_subject__gender'.format(self.visit_attr),
#                      'dob': '{}__appointment__registered_subject__dob'.format(self.visit_attr),
#                      'visit_reason': '{}__reason.format(self.visit_attr)'.format(self.visit_attr),
#                      'visit_status': '{}__appointment__appt_status'.format(self.visit_attr),
#                      'visit': '{}__appointment__visit_definition__code'.format(self.visit_attr),
#                      'visit_instance': '{}__appointment__visit_instance'.format(self.visit_attr)}),
#             ),
#             'export_as_csv_action',
#             'Export to CSV with visit and demographics')
#         return actions


class VisitAdminMixin(object):

    """ModelAdmin subclass for models with a ForeignKey to 'appointment', such as your visit model(s).

    In the child ModelAdmin class set the following attributes, for example::

        visit_attr = 'maternal_visit'
        dashboard_type = 'maternal'

    """
    date_hierarchy = 'report_datetime'

    def __init__(self, *args, **kwargs):
        super(VisitAdminMixin, self).__init__(*args, **kwargs)

        self.fields = [
            'appointment',
            'report_datetime',
            'reason',
            'reason_missed',
            'study_status',
            'require_crfs',
            'info_source',
            'info_source_other',
            'comments'
        ]
        if issubclass(self.model, CaretakerFieldsMixin):
            self.fields.pop(self.fields.index('comments'))
            self.fields.extend([
                'information_provider',
                'information_provider_other',
                'is_present',
                'survival_status',
                'last_alive_date',
                'comments'])

        self.list_display = ['appointment', 'report_datetime', 'reason', 'study_status', 'created',
                             'modified', 'user_created', 'user_modified', ]

        self.search_fields = ['id', 'reason', 'appointment__visit_code',
                              'appointment__subject_identifier']

        self.list_filter = ['study_status',
                            'appointment__visit_instance',
                            'reason',
                            'appointment__visit_code',
                            'report_datetime',
                            'created',
                            'modified',
                            'user_created',
                            'user_modified',
                            'hostname_created']
        self.radio_fields = {'require_crfs': admin.VERTICAL}
        if issubclass(self.model, CaretakerFieldsMixin):
            self.radio_fields.update({
                # 'information_provider': admin.VERTICAL,
                'is_present': admin.VERTICAL,
                'survival_status': admin.VERTICAL,
            })

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'appointment' and request.GET.get('appointment'):
            kwargs["queryset"] = self.appointment.__class__.objects.filter(pk=request.GET.get('appointment', 0))
        return super(VisitAdminMixin, self).formfield_for_foreignkey(db_field, request, **kwargs)