# Architecture & System Design 🏗️

This document defines the architectural boundaries and design patterns for the Maritime Port Sandbox. As an autonomous agent, you must strictly adhere to these patterns when generating or refactoring code.

## 1. System Overview
The Sandbox is a deterministic Mock API built with **FastAPI**. It does not connect to real physical ports. Its sole purpose is to hold a simulated state of European maritime ports and return this state using industry-standard (DCSA) JSON schemas.

The system is designed around two conflicting personas:
1. **The Autonomous SCM Agent (Consumer):** Reads the port status via the Public API.
2. **The Simulation Controller (Admin):** Mutates the port status (injects chaos) via the Admin API.

## 2. Directory Structure & Layered Design
We follow a strict layered architecture. Do not bypass layers (e.g., routers must not manipulate state directly; they must call a service).

```text
src/
├── api/                  # FastAPI Routers (Transport Layer)
│   ├── public/           # Consumer-facing DCSA endpoints (e.g., /api/v1/pcs/...)
│   └── admin/            # Chaos injection endpoints (e.g., /admin/simulation/...)
├── services/             # Business Logic & State orchestration
│   └── port_manager.py   # Handles get/update logic for port states
├── schemas/              # Pydantic v2 Models (Strict validation)
│   ├── dcsa.py           # Standardized output models (read docs/domain/dcsa-standards.md)
│   └── admin.py          # Input models for chaos injection
├── core/                 # App configuration, dependency injection
└── state/                # In-memory data store (The "Database")

## 3. Runtime Host Targeting
For multi-machine deployments in this project:

1. Do not use `localhost` in examples, checks, or runbooks.
2. Assume the sandbox is hosted on `skz-data-lv`.
3. Resolve host/IP from `DEV_NODE_IP` in `.env` and call the API as `http://${DEV_NODE_IP}:8001/...`.
4. Keep private IPs and secrets out of docs; store them in `.env` only.