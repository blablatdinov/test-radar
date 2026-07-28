# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaetdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import datetime
import logging
import secrets

import bcrypt

from records.models import Agent, ApiToken

logger = logging.getLogger('records.token')

_TOKEN_LENGTH = 32
_MASK_PREFIX_LENGTH = 6
_CI_PREFIX = 'ci_'
_DEV_PREFIX = 'dev_'
_UNDERSCORE = '_'


def _generate_raw_token(agent_type: str) -> str:
    prefix = _CI_PREFIX if agent_type == Agent.AgentType.CI else _DEV_PREFIX
    return prefix + secrets.token_urlsafe(_TOKEN_LENGTH)


def mask_token(raw_token: str) -> str:
    if len(raw_token) <= _MASK_PREFIX_LENGTH:
        return raw_token
    return f'{raw_token[:_MASK_PREFIX_LENGTH]}...{raw_token[-3:]}'


def _hash_token(raw_token: str) -> str:
    return bcrypt.hashpw(raw_token.encode(), bcrypt.gensalt()).decode()


def _extract_prefix(raw_token: str) -> str:
    if _UNDERSCORE not in raw_token:
        return ''
    return raw_token.split(_UNDERSCORE, maxsplit=1)[0] + _UNDERSCORE


def create_token_for_agent(agent: Agent) -> str:
    raw_token = _generate_raw_token(agent.type)
    ApiToken.objects.create(
        agent=agent,
        token_hash=_hash_token(raw_token),
        token_mask=mask_token(raw_token),
    )
    logger.info('Token created for agent %r (type=%s)', agent.name, agent.type)
    return raw_token


def regenerate_token_for_agent(agent: Agent) -> str:
    if hasattr(agent, 'token'):
        agent.token.delete()
        logger.info('Old token deleted for agent %r', agent.name)
    return create_token_for_agent(agent)


def verify_token(raw_token: str) -> ApiToken | None:
    prefix = _extract_prefix(raw_token)
    candidates = ApiToken.objects.select_related('agent').filter(
        token_mask__startswith=prefix,
    )
    now = datetime.datetime.now(tz=datetime.UTC)
    for candidate in candidates:
        if candidate.expires_at is not None and candidate.expires_at < now:
            logger.debug('Skipping expired token %s for agent %r', candidate.token_mask, candidate.agent.name)
            continue
        if bcrypt.checkpw(raw_token.encode(), candidate.token_hash.encode()):
            logger.debug('Token %s verified for agent %r', candidate.token_mask, candidate.agent.name)
            return candidate
    logger.debug('No matching token found for prefix %r', prefix)
    return None
