# Fakenodo (local Zenodo-like test service)

A tiny HTTP service that mimics a minimal subset of Zenodo's depositions API to develop and test UVLHub/PadelHub integrations without hitting the real Zenodo API.

- Endpoints implemented (under `/api/deposit/depositions`):
  - `GET /` — list depositions
  - `POST /` — create new deposition from `{"metadata": {...}}`
  - `GET /<id>` — get a deposition
  - `PUT /<id>` — update deposition metadata (draft)
  - `DELETE /<id>` — delete a deposition
  - `POST /<id>/files` — upload a file or zip (multipart form: name + file)
  - `POST /<id>/actions/edit` — switch to editable draft (always 201)
  - `POST /<id>/actions/publish` — publish; creates or reuses DOI depending on file changes
  - `GET /<id>/versions` — list published versions/DOIs

- Versioning/DOI rules:
  - First publish creates version 1 with DOI `10.5072/fakenodo.<id>.v1`.
  - Subsequent publish:
    - If only metadata changed AND files are the same, it reuses the latest DOI/version (no bump).
    - If files changed (added/modified) then a new version/DOI is created.

- Data storage: JSON file at `app/modules/fakenodo/data/store.json` plus uploaded files under `app/modules/fakenodo/data/uploads/`.

## Run locally

```bash
python3 app/modules/fakenodo/app.py
# defaults to port 5055
```

Health check:

```bash
curl http://127.0.0.1:5055/health
```

## Configure UVLHub/PadelHub to use it

Set the environment variable `FAKENODO_URL` to point to the base depositions endpoint:

```
FAKENODO_URL=http://127.0.0.1:5055/api/deposit/depositions
```

Both `app/` and `uvlhub/` code paths will prefer `FAKENODO_URL` over `ZENODO_API_URL` automatically.

## Quick manual test

```bash
# 1) Create deposition
curl -s -X POST http://127.0.0.1:5055/api/deposit/depositions \
  -H 'Content-Type: application/json' \
  -d '{"metadata": {"title": "Test", "upload_type": "dataset"}}'

# 2) Upload file (replace <id> from previous response)
curl -s -X POST http://127.0.0.1:5055/api/deposit/depositions/<id>/files \
  -F name=test.txt -F file=@/etc/hosts

# 3) Publish
curl -s -X POST http://127.0.0.1:5055/api/deposit/depositions/<id>/actions/publish

# 4) List versions
curl -s http://127.0.0.1:5055/api/deposit/depositions/<id>/versions | jq
```

## Notes

- This service is intentionally simple. It is not Zenodo; it just behaves sufficiently similar for our workflows.
- You can change the DOI prefix by setting `FAKENODO_DOI_PREFIX`.
