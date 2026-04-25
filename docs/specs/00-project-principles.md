# Project Principles — Meta Ads Ultimate Dashboard

> **Document ID:** 00_PROJECT_PRINCIPLES
> **Version:** 1.0.0
> **Methodology:** BMAD (Build More Architect Dreams) + SPEKIT (Spec-Driven Development)
> **Status:** Canonical

---

## Purpose

This document defines the governing principles of the Meta Ads Ultimate Dashboard.
Every architectural decision, module interface, and line of code must conform to these principles.

---

## Principle 1: Edge Configuration Sovereignty

All configuration lives at the edge — in local files, environment variables, or user-supplied config JSONs.
No configuration is fetched from a remote server at runtime.

- `ConfigStore` reads only from local filesystem paths, environment variables, or CLI arguments.
- Secrets (Meta API tokens, Google service account credentials) are read from `.env` files or environment variables.
- Config validation runs against bundled schemas, not remote endpoints.

## Principle 2: Nothing Is Mandatory

No single data source, module, or feature is required for the system to function.
The system degrades gracefully:

- If Google Sheets is not configured, the dashboard still shows ad data.
- If Meta Ads is not configured, the dashboard shows an empty state with setup guidance.
- Every module beyond core `Config` and `Dashboard` is optional.

## Principle 3: Brand Isolation

Each brand's data, configuration, cache, and dashboard state are completely isolated.
A bug in Brand A must never affect Brand B.

## Principle 4: View-Only External Data Sources

The system never writes to external data sources (Google Sheets, Meta API campaign modifications)
unless explicitly requested through dedicated management pages.
The extraction engine is strictly read-only.

## Principle 5: Transparent Data Pipeline

Every transformation step is logged and auditable.
Raw API responses are preserved alongside processed outputs.

## Principle 6: Fail-Soft Execution

When an API call, breakdown combination, or metric request fails:

- Log the failure with full context.
- Continue processing remaining tasks.
- Include failure metadata in the manifest.
- Never crash the entire extraction run due to a single failure.

## Principle 7: Local-First, Free-Forever

The system runs entirely on the user's machine with zero cloud dependencies.
No SaaS subscriptions, no usage limits, no data leaves the local machine.

## Principle 8: GUI-First Configuration

All configuration that a non-developer user might need to change is editable
through the dashboard GUI. CLI/file editing is available but never required.
