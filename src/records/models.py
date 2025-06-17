import secrets

from django.db import models
from django.utils.translation import gettext_lazy as _


def _hex_token() -> str:
    return secrets.token_hex(16)


class TestRecord(models.Model):
    id = models.CharField(
        _('Indentifier'),
        primary_key=True,
        max_length=32,
        default=_hex_token,
    )
    label = models.CharField(_('Label'), max_length=128)
    success = models.BooleanField(_('Success'))
    timestamp = models.DateTimeField(_('Timestamp'))
    # TODO: logs field
    # logs = ...

    class Meta:
        verbose_name = _('Test record')
        verbose_name_plural = _('Test records')

    def __str__(self) -> str:
        return str(self.label)
