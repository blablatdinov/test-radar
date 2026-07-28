# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaletdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import secrets

import bcrypt

from records.models import Agent, ApiToken

_TOKEN_LENGTH = 32
_MASK_PREFIX_LENGTH = 6
_CI_PREFIX = 'ci_'
_DEV_PREFIX = 'dev_'
_UNDERSCORE = '_'


def _generate_raw_token(agent_type: str) -> str:
    prefix = _CI_PREFIX if agent_type == Agent.AgentType.CI else _DEV_PREFIX
    return prefix + secrets.token_urlsafe(_TOKEN_LENGTH)


def _mask_token(raw_token: str) -> str:
    if len(raw_token) <= _MASK_PREFIX_LENGTH:
        return raw_token
    prefix_part = raw_token[:_MASK_PREFIX_LENGTH]
    return f'{prefix_part}...'


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
        token_mask=_mask_token(raw_token),
    )
    return raw_token


def regenerate_token_for_agent(agent: Agent) -> str:
    if hasattr(agent, 'token'):
        agent.token.delete()
    return create_token_for_agent(agent)


def verify_token(raw_token: str) -> ApiToken | None:
    prefix = _extract_prefix(raw_token)
    candidates = ApiToken.objects.select_related('agent').filter(
        token_mask__startswith=prefix,
    )
    for candidate in candidates:
        if bcrypt.checkpw(raw_token.encode(), candidate.token_hash.encode()):
            return candidate
    return None
