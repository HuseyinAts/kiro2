"""E2E (golden_flow) test conftest.

KOD GERCEGI (golden-flow 185/185 setup coksusu):
pytest.ini `asyncio_default_fixture_loop_scope = session` AYARLI, ama requirements
`pytest-asyncio==0.21.1` sabitliyor — o ayar 0.24+'ta geldi, 0.21.1 YOK SAYAR.
Kok conftest'teki session-kapsamli async autouse fixture'lar (ornegin
`global_db_manager_cleanup`) 0.21.1'de session-kapsamli bir `event_loop` ISTER;
yoksa xdist worker'inda ScopeMismatch olur ve golden_flow testlerinin HEPSI
setup'ta duser (185 hata). Bu fixture yalniz tests/e2e/ altinda gecerli — zorunlu
(ders-zorlayici) test setini ETKILEMEZ.
"""

import asyncio

import pytest


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
