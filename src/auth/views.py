# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import TYPE_CHECKING

from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import FormView
from django_ratelimit.decorators import ratelimit

from auth.forms import RegistrationForm

if TYPE_CHECKING:
    from django.http import HttpResponse


class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    """Custom logout view."""


@method_decorator(ratelimit(key='ip', rate='5/h', block=True), name='dispatch')
class RegisterView(FormView):
    template_name = 'register.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('index_page')

    def form_valid(self, form: RegistrationForm) -> HttpResponse:
        user = form.save()
        login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
        return super().form_valid(form)


# TODO #6:30min Create view for generate agent tokens
