# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaetdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import datetime
import logging

from django.http import HttpRequest
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from records.srv.token import verify_token

_TOKEN_PREFIX = 'Token '
_INVALID_TOKEN_MSG = 'Invalid agent token.'

logger = logging.getLogger('api.authentication')


class AgentTokenAuthentication(BaseAuthentication):
    """Authenticate agents via 'Authorization: Token <raw_token>' header."""

    keyword = 'Token'

    def authenticate(self, request: HttpRequest) -> tuple | None:
        header = request.META.get('HTTP_AUTHORIZATION', '')
        if not header.startswith(_TOKEN_PREFIX):
            return None
        raw_token = header[len(_TOKEN_PREFIX):].strip()
        if not raw_token:
            logger.warning('Empty token in Authorization header from %s', request.META.get('REMOTE_ADDR'))
            return None
        logger.debug('Verifying agent token from %s', request.META.get('REMOTE_ADDR'))
        api_token = verify_token(raw_token)
        if api_token is None:
            logger.warning(
                'Invalid agent token rejected from %s',
                request.META.get('REMOTE_ADDR'),
            )
            raise AuthenticationFailed(_INVALID_TOKEN_MSG)
        logger.info(
            'Agent %r authenticated via token %s',
            api_token.agent.name,
            api_token.token_mask,
        )
        api_token.last_used_at = datetime.datetime.now(tz=datetime.UTC)
        api_token.last_used_ip = request.META.get('REMOTE_ADDR')
        api_token.save(update_fields=['last_used_at', 'last_used_ip'])
        return (api_token.agent.owner, api_token)

    def authenticate_header(self, _request: HttpRequest) -> str:
        return self.keyword
