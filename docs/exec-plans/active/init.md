# Инициация Maritime Port Sandbox (первичная реализация)

## Summary
Собрать минимально-полноценный детерминированный Mock API на FastAPI по архитектуре из `docs/architecture/index.md`, с DCSA-схемами и бизнес-правилами из `docs/domain/dcsa-standards.md`: публичное чтение статуса порта + admin “chaos injection”, полностью покрыто тестами и проверяемо `ruff`/`mypy`.

## Key Changes
### 1) Каркас проекта и tooling
- Добавить `pyproject.toml` (только конфиги инструментов): `ruff`, `mypy`, `pytest` (Python 3.11+, строгая типизация по умолчанию).
- Добавить `requirements.txt` (runtime) и `requirements-dev.txt` (dev: ruff/mypy/pytest и пр.), чтобы Quick Start оставался через `pip install -r requirements.txt`.
- Добавить `main.py` в корне: `app = create_app()`, чтобы работало `uvicorn main:app --reload --port 8000`.

### 2) Реализация слоёв по `docs/architecture`
Создать структуру `src/` и строго соблюдать “router → service → state”:
- `src/schemas/dcsa.py`: Pydantic v2 модели **строго** по `docs/domain/dcsa-standards.md` (strict + forbid extra), включая `OperationalStatus`, `TerminalMetrics`, `PortStatusResponse`.
- `src/schemas/admin.py`: модели для admin API:
  - `ChaosScenarioType`: `STORM_SURGE | LABOR_STRIKE | YARD_CONGESTION`
  - `Severity`: `LOW | MEDIUM | HIGH` (совместимо с README-примером), default `MEDIUM`
  - `InjectScenarioRequest`: `targetPort`, `scenarioType`, `severity`
- `src/state/`: in-memory “DB”
  - Константы поддерживаемых портов и max capacity (DEHAM/NLRTM/BEANR) из таблицы в `docs/domain/dcsa-standards.md`.
  - Хранилище состояний + синхронизация (lock).
  - Детерминированные стартовые значения метрик (одинаковые между перезапусками).
  - Детерминированные `updatedAt`: “симуляционные часы” (старт `2026-01-01T00:00:00Z`, +1 секунда на каждую **успешную мутацию** порта).
- `src/services/port_manager.py`:
  - `get_port_status(port_code) -> PortStatusResponse` (404 если порт не поддержан).
  - `inject_scenario(req) -> PortStatusResponse` с enforce-правилами:
    - **Closure Rule**: если статус `CLOSED` → `availableCapacityTEU=0` немедленно.
    - **Density Rule**: если `yardDensityPercent > 85.0` и было `NORMAL` → `RESTRICTED`.
    - **Spillover Cap**: `availableCapacityTEU <= max_capacity`.
  - Детерминированные эффекты сценариев:
    - `STORM_SURGE`: `operationalStatus=CLOSED`, `availableCapacityTEU=0`, `yardDensityPercent` **без изменений**, `availableReeferPlugs` **без изменений**
    - `LABOR_STRIKE`: `operationalStatus=RESTRICTED`, `yardDensityPercent=80.0`, `availableCapacityTEU=floor(max*0.5)`, `availableReeferPlugs` без изменений
    - `YARD_CONGESTION`: `yardDensityPercent` = 91/93/96 для LOW/MEDIUM/HIGH, `availableCapacityTEU=floor(max*0.7/0.5/0.3)`, статус доводится правилами
- `src/api/public/...`:
  - `GET /api/v1/pcs/terminals/{portCode}/status` → `PortStatusResponse`
- `src/api/admin/...`:
  - `POST /admin/simulation/scenario` → возвращает обновлённый `PortStatusResponse`
  - Видимость в OpenAPI: по флагу `EXPOSE_ADMIN_DOCS` (по умолчанию скрыто, при `EXPOSE_ADMIN_DOCS=1` видно в `/docs`).
- `src/core/`:
  - `create_app()` (FastAPI app factory), подключение роутеров, DI для `PortManager`, чтение env `EXPOSE_ADMIN_DOCS`.

### 3) Документация
- Обновить `README.md` под реальную структуру (зависимости/запуск, описание `EXPOSE_ADMIN_DOCS`, curl-примеры).
- Создать `docs/exec-plans/active/init.md` и сохранить туда этот план (как “ground truth” исполнения).

## Test Plan (pytest)
- Unit-тесты `PortManager`:
  - неподдерживаемый порт → 404.
  - `STORM_SURGE`: capacity=0, статус CLOSED, `yardDensityPercent` не меняется.
  - `YARD_CONGESTION`: `yardDensityPercent > 90` и статус становится `RESTRICTED` (если был `NORMAL`).
  - `availableCapacityTEU` никогда не превышает max capacity.
  - `updatedAt` детерминированно стартует и инкрементируется на мутациях.
- API-тесты (FastAPI TestClient):
  - `GET /api/v1/pcs/terminals/DEHAM/status` валиден по DCSA-модели.
  - `POST /admin/simulation/scenario` мутирует состояние и возвращает новое.
  - OpenAPI: admin-роуты отсутствуют при `EXPOSE_ADMIN_DOCS=0` и присутствуют при `EXPOSE_ADMIN_DOCS=1`.

## Assumptions / Defaults
- `updatedAt` — детерминированное “симуляционное” время: старт `2026-01-01T00:00:00Z`, +1s на успешную мутацию порта.
- Зависимости: `requirements*.txt`; конфиги инструментов: `pyproject.toml`.
- Admin-эндпоинты функционально доступны всегда, но отображаются в Swagger/OpenAPI только при `EXPOSE_ADMIN_DOCS=1`.

