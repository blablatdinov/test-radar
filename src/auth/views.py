# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING, Any

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView
from django_ratelimit.decorators import ratelimit

from auth.forms import RegistrationForm
from auth.services import create_confirmation_token, send_confirmation_email

if TYPE_CHECKING:
    from django.http import HttpResponse


class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def form_valid(self, form: Any) -> HttpResponse:
        user = form.get_user()
        if not user.is_email_verified:
            form.add_error(
                None,
                _('Please confirm your email address to log in.'),
            )
            return self.form_invalid(form)
        return super().form_valid(form)


class CustomLogoutView(LogoutView):
    """Custom logout view."""


@method_decorator(ratelimit(key='ip', rate='5/h', block=True), name='dispatch')
class RegisterView(FormView):
    template_name = 'register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('email_confirmation_sent')

    def form_valid(self, form: RegistrationForm) -> HttpResponse:
        user = form.save()
        token = create_confirmation_token(user)
        send_confirmation_email(self.request, token)
        return super().form_valid(form)
