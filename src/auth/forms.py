# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from auth.models import User


class RegistrationForm(forms.Form):
    username = forms.CharField(
        label=_('Username'),
        max_length=150,
    )
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label=_('Confirm password'),
        widget=forms.PasswordInput,
    )

    def clean_username(self) -> str:
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(_('A user with this username already exists.'))
        return username

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Passwords do not match.'))
        if password1:
            validate_password(password1)
        return cleaned_data

    def save(self) -> User:
        return User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password1'],
        )
