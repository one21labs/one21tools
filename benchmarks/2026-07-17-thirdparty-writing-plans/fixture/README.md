# taskboard

A small team task-tracking HTTP API (Flask). Tasks belong to users; auth is a static
per-user token header (`X-Auth-Token`). Storage is a single JSON file on disk.

Run: `pip install -r requirements.txt && python -m taskboard.app`
Test: `pytest tests/`
