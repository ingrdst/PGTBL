from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone

# App imports
from core.permissions import PermissionMixin
from disciplines.models import Discipline
from modules.models import TBLSession
from grat.forms import GRATDateForm

# Python imports
from datetime import timedelta

from notification.models import Notification


class GRATDateUpdateView(LoginRequiredMixin,
                         PermissionMixin,
                         UpdateView):
    """
    Update the gRAT date.
    """

    model = TBLSession
    template_name = 'grat/grat.html'
    form_class = GRATDateForm

    # Permissions
    permissions_required = ['crud_tests']

    def get_discipline(self):
        """
        Get the discipline from url kwargs.
        """

        discipline = Discipline.objects.get(
            slug=self.kwargs.get('slug', '')
        )

        return discipline

    def form_valid(self, form):
        """
        Return the form with fields valided.
        """

        now = timezone.localtime(timezone.now())

        if form.instance.grat_datetime is None:

            messages.error(
                self.request,
                _("gRAT date must to be filled in.")
            )

            return redirect(self.get_success_url())

        if now > form.instance.grat_datetime:

            messages.error(
                self.request,
                _("gRAT date must to be later than today's date.")
            )

            return redirect(self.get_success_url())

        if (form.instance.irat_datetime + timedelta(minutes=form.instance.irat_duration)) > form.instance.grat_datetime:

            messages.error(
                self.request,
                _("gRAT date must to be later than iRAT date with its duration.")
            )

            return redirect(self.get_success_url())

        messages.success(self.request, _('gRAT date updated successfully.'))

        self.send_notification(form)

        return super(GRATDateUpdateView, self).form_valid(form)

    def send_notification(self, form):
        """
        Send notification to all students
        """

        discipline = self.get_discipline()
        session = self.get_object()

        description = _("gRAT date update to {0} from session {1}".format(
            form.instance.irat_datetime.strftime("%d/%m/%Y às %H:%M"),
            session.title
        ))

        for student in discipline.students.all():
            Notification.objects.create(
                title=_("gRAT date updated"),
                description=description,
                sender=discipline.teacher,
                receiver=student,
                discipline=discipline
            )

    def get_success_url(self):
        """
        Get success url to redirect.
        """

        success_url = reverse_lazy(
            'grat:list',
            kwargs={
                'slug': self.kwargs.get('slug', ''),
                'pk': self.kwargs.get('pk', '')
            }
        )

        return success_url
