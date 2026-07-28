# SPDX-FileCopyrightText: Copyright (c) 2025-2026 Almaz Ilaetdinov <a.ilaletdinov@yandex.ru>
# SPDX-License-Identifier: MIT

import secrets
from records.srv.token import mask_token


def test_mask_token():
    got = mask_token('dev_qGhTxSaRcxv3rK6ji-pWaEjs5ATa3QJHf49ZUUm6HR4')

    assert got == 'dev_qG...HR4'
