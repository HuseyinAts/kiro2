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


# GUNCELLEME (6 Eyl 2026, SS10.56): bu override pytest-asyncio 0.21.1
# icin yazilmisti (o surum asyncio_default_fixture_loop_scope'u yok
# sayiyordu). Depo artik 1.3.0'a tasindi; 1.x'te kullanicinin event_loop
# override etmesi KALDIRILDI ve teardown'daki loop.close() plugin'in hala
# kullandigi loop'u kapatip sonraki async testleri
# 'RuntimeError: Event loop is closed' ile dusuruyordu.
