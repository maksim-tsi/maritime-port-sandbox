# Agent Directives: Maritime Port Sandbox ⚓️

Welcome. You are an autonomous AI coding agent operating in an "Agent-First" repository. Your primary directive is to execute tasks, write code, tests, and maintain documentation without requiring humans to write code manually.

This file is your **Map**, not your encyclopedia. For detailed context, always refer to the `docs/` directory.

## 1. Core Beliefs & Operating Principles
* **Determinism over Realism:** This is a Mock API (Sandbox). It must return perfectly predictable, DCSA-compliant data, not real-world scraped data.
* **Agent Legibility:** Write code that is easy for *you* (and future agents) to read and refactor. 
* **Mechanical Enforcement:** Rely on our CI, `ruff`, `mypy`, and `pytest`. If a linter fails, read the error and fix the code. Do not ignore static typing.
* **No Manual Code:** Humans will guide you via prompts, PR comments, and architectural constraints. You write the code.

## 2. Knowledge Map (Where to find things)
Before starting a complex task, read the relevant documentation in the `/docs` directory:

* **`/docs/architecture/index.md`** - System design, FastAPI layer structure, and dependency injection rules.
* **`/docs/domain/dcsa-standards.md`** - JSON schemas and business logic for Digital Container Shipping Association (DCSA) standards.
* **`/docs/exec-plans/active/`** - Step-by-step execution plans for current features. Always update your progress here.
* **`/docs/decisions/`** - Architectural Decision Records (ADRs). Why we chose specific libraries or patterns.

## 3. Workflow Instructions
When assigned a task, follow this exact Ralph Wiggum Loop:
1. **Discover:** Read the task, then read the relevant files in `/docs` and the existing codebase.
2. **Plan:** If the task is complex, write a markdown plan in `/docs/exec-plans/active/` before writing code.
3. **Execute:** Implement the feature. You must write or update `pytest` tests for every logic change.
4. **Validate:** Run `pytest` and linters (`ruff check .`). Fix all errors yourself. 
5. **Document:** If you change the API, update the OpenAPI spec/FastAPI docstrings and relevant `/docs` files.

## 4. Tech Stack Constraints
* **Language:** Python 3.11+
* **Framework:** FastAPI
* **Validation:** Pydantic v2 (Strict mode preferred)
* **Testing:** Pytest (100% coverage expected for core domain logic)

## 5. Runtime Host Targeting (Important)
* **Never use `localhost` in project documentation, examples, validation commands, or agent runbooks for network access.**
* Assume the Maritime Port Sandbox runs on **`skz-data-lv`**.
* Resolve the target IP from **`DEV_NODE_IP`** in `.env` and build URLs as `http://${DEV_NODE_IP}:8001/...`.
* Keep private values in `.env` only (gitignored). Do not commit concrete private IPs.

*End of Directives. Look at the task and begin your discovery phase.*