# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any, final

from django import forms
from django.utils.translation import gettext_lazy as _

from auth.models import User
from records.models import Agent, Membership, Project

_IDENTIFIER_MAX_LENGTH = 150


@final
class ProjectForm(forms.ModelForm):
    @final
    class Meta:
        model = Project
        fields = ('name',)


@final
class AgentForm(forms.ModelForm):
    def __init__(self, *args: Any, project: Project | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._project = project

    @final
    class Meta:
        model = Agent
        fields = ('name', 'type')

    def clean_name(self) -> str:
        name = self.cleaned_data['name']
        if (
            self._project is not None and Agent.objects.filter(
                name=name,
                project=self._project,
            ).exists()
        ):
            raise forms.ValidationError(_('An agent with this name already exists in this project.'))
        return name


@final
class AddMemberForm(forms.Form):
    def __init__(self, *args: Any, project: Project | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._project = project

    identifier = forms.CharField(
        label=_('Username or email'),
        max_length=_IDENTIFIER_MAX_LENGTH,
    )
    role = forms.ChoiceField(
        label=_('Role'),
        choices=[
            (Membership.Role.DEVELOPER, _('Developer')),
            (Membership.Role.MAINTAINER, _('Maintainer')),
        ],
    )

    def clean_identifier(self) -> str:
        identifier = self.cleaned_data['identifier']
        if self._project is None:
            return identifier
        user = self._find_user(identifier)
        if user is None:
            # @todo #182:30min Implement invite flow for non-existent users.
            #  When a user with the given email/username does not exist, send
            #  an invitation email instead of showing an error.
            raise forms.ValidationError(_('User not found.'))
        if Membership.objects.filter(user=user, project=self._project).exists():
            raise forms.ValidationError(_('This user is already a member of the project.'))
        return identifier

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean() or {}
        identifier = cleaned_data.get('identifier')
        if identifier and self._project is not None:
            user = self._find_user(identifier)
            if user is not None:
                cleaned_data['user'] = user
        return cleaned_data

    def _find_user(self, identifier: str) -> User | None:
        if self._project is None:
            return None
        by_email = User.objects.filter(email=identifier)
        by_username = User.objects.filter(username=identifier)
        return (by_email | by_username).first()
