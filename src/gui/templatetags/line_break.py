# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def line_break(test_label: str) -> str:
    return format_html('{}', test_label.replace('_', '_\u200B'))
