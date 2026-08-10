# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from typing import Any

from django import forms
from django.utils.translation import gettext_lazy as _

from records.models import Agent, Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('name',)


class AgentForm(forms.ModelForm):
    def __init__(self, *args: Any, project: Project | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._project = project

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
