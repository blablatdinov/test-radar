# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def line_break(value):
    return mark_safe(value.replace('_', '_\u200B'))
