# Task 1 Report: Provider/Format Configuration Model and Migration

## Changed files

- `backend/app/core/config_manager.py`: added canonical provider/format constants, normalization and validation helpers, legacy `llm_mode` migration, canonical defaults, migration-required tracking, and rejection of legacy writes.
- `backend/app/schemas/setup.py`: added canonical provider/format fields, strict extra-field handling, provider/format validation, and Azure/unknown-provider rejection.
- `backend/app/api/v1/setup.py`: persists canonical provider/format fields during setup.
- `backend/app/api/v1/config.py`: rejects `llm_mode` updates.
- `backend/app/api/v1/dashboard.py`: returns canonical provider/format/migration fields with legacy fallback and provider-based Ollama dependency status.
- `backend/app/core/settings.py`: added canonical provider/format settings defaults.
- `backend/tests/test_config_manager.py`: covered canonical defaults, legacy local/Azure migration, normalization, validation, and canonical cloud-provider updates.
- `backend/tests/api/test_auth_setup.py`: updated setup payloads and covered legacy/Azure rejection.
- `backend/tests/api/test_config.py`: updated canonical setup, covered legacy-write and provider/format rejection, and dashboard fields.

## Tests

Commands run from `backend/`:

```text
python3 -m pytest -q tests/test_config_manager.py tests/api/test_auth_setup.py tests/api/test_config.py
16 passed, 10 warnings in 6.29s

python3 -m pytest -q
31 passed, 11 warnings in 7.19s
```

Warnings are existing dependency deprecations from `passlib`/`python-jose`.

## Commit

Implementation commit: `1d8dc36b070cb5807947ccbbb1d953bdb83be155`

## Concerns

- `llm_mode` remains in `Settings` and is available when reading legacy database rows for compatibility, but it is no longer seeded or writable through the new setup/configuration APIs.
- Existing application-level validation error handling can expose only the generic validation message for schema-level errors; endpoint/config-manager validation preserves the established detailed API-key message.
