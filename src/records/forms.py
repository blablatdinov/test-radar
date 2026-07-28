# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django import forms

from records.models import Agent, Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ('name',)


class AgentForm(forms.ModelForm):
    class Meta:
        model = Agent
        fields = ('name', 'type')
