# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import uuid
from typing import final

from django.contrib import messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import FormView, TemplateView

from auth import services
from auth.forms import EmailResendForm
from auth.models import EmailConfirmationToken, User


@final
class EmailConfirmationSentView(TemplateView):
    template_name = 'email_confirmation_sent.html'


@final
class EmailConfirmView(View):
    def get(self, request: HttpRequest, token: uuid.UUID) -> HttpResponse:
        try:
            confirmation_token = (
                EmailConfirmationToken.objects
                .select_related('user')
                .only('expired_at', 'user', 'user__is_email_verified')
                .get(token=token)
            )
        except EmailConfirmationToken.DoesNotExist:
            return self._render_invalid(request)

        if confirmation_token.is_expired():
            confirmation_token.delete()
            return self._render_invalid(request)

        user = confirmation_token.user
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])
        confirmation_token.delete()
        messages.success(request, _('Your email has been confirmed. You can now log in.'))
        return redirect('login')

    def _render_invalid(self, request: HttpRequest) -> HttpResponse:
        messages.error(request, _('The confirmation link is invalid or has expired.'))
        return redirect('email_resend')


@final
class EmailResendView(FormView):
    template_name = 'email_resend.html'
    form_class = EmailResendForm
    success_url = reverse_lazy('email_confirmation_sent')

    def form_valid(self, form: EmailResendForm) -> HttpResponse:
        email = form.cleaned_data['email']
        try:
            user = User.objects.only('id', 'email').get(email=email, is_email_verified=False)
        except User.DoesNotExist:
            return HttpResponseRedirect(self.get_success_url())
        token = services.create_confirmation_token(user)
        services.send_confirmation_email(self.request, token)
        return super().form_valid(form)
