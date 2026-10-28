"""File a dated amendment on the OSF registration as a registration revision.

The amendment text is appended to the registration's amendments block (``344-86``) of the latest
approved revision, after a blank line, as Amendments 3-5 were. The write path is OSF's
undocumented one, learned filing Amendments 2-5 and recorded here so it need not be relearned:

1. create: POST ``/v2/schema_responses/`` (top level; the nested route is 405) with JSON:API type
   ``schema-responses`` and the registration as a relationship;
2. fill: PATCH ``/v2/schema_responses/<id>/`` with ``revision_justification`` and
   ``revision_responses``;
3. move: POST ``/v2/schema_responses/<id>/actions/`` with trigger ``submit``, then ``approve``
   (not ``accept``), and a ``target`` relationship -- a PATCHed trigger returns 200 and does
   nothing.

The token is ``~/.config/osf/token``. ``--dry-run`` reads and prints what would be written.

Usage::

    python scripts/osf_amend.py paper/amendment-006-osf-text.md "Amendment 6 ..." [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

API = "https://api.osf.io/v2"
REGISTRATION = "6ugxc"
BLOCK = "344-86"
TOKEN = Path.home() / ".config/osf/token"


def call(method: str, path: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN.read_text().strip()}",
            "Content-Type": "application/vnd.api+json",
        },
    )
    with urllib.request.urlopen(req) as r:
        raw = r.read()
    return json.loads(raw) if raw else {}


def amendment_body(path: Path) -> str:
    """The registration text: everything after the file's first ``---`` rule."""
    text = path.read_text(encoding="utf-8")
    return text.split("\n---\n", 1)[1].strip()


def latest() -> dict:
    data = call("GET", f"/registrations/{REGISTRATION}/schema_responses/")["data"]
    approved = [r for r in data if r["attributes"]["reviews_state"] == "approved"]
    pending = [r for r in data if r["attributes"]["reviews_state"] != "approved"]
    if pending:
        raise SystemExit(f"a revision is already open: {pending[0]['id']}")
    return max(approved, key=lambda r: r["attributes"]["date_created"])


def act(sid: str, trigger: str) -> None:
    target = {"data": {"type": "schema-responses", "id": sid}}
    call("POST", f"/schema_responses/{sid}/actions/", {"data": {
        "type": "schema-response-actions", "attributes": {"trigger": trigger},
        "relationships": {"target": target}}})  # fmt: skip


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("text", type=Path)
    ap.add_argument("justification")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    body = amendment_body(a.text)
    head = latest()
    old = head["attributes"]["revision_responses"][BLOCK]
    first = body.split("\n", 1)[0][:60]
    if first in old:
        raise SystemExit(f"already in the registration: {first!r}")
    new = old.rstrip() + "\n\n" + body
    print(f"latest approved {head['id']}; block {BLOCK}: {len(old):,} -> {len(new):,} chars")
    if a.dry_run:
        print(body[:400] + " ...")
        return 0
    reg = {"data": {"type": "registrations", "id": REGISTRATION}}
    created = call("POST", "/schema_responses/", {"data": {
        "type": "schema-responses", "relationships": {"registration": reg}}})  # fmt: skip
    sid = created["data"]["id"]
    print(f"created revision {sid}")
    call("PATCH", f"/schema_responses/{sid}/", {"data": {"type": "schema-responses", "id": sid,
         "attributes": {"revision_justification": a.justification,
                        "revision_responses": {BLOCK: new}}}})  # fmt: skip
    act(sid, "submit")
    act(sid, "approve")
    got = call("GET", f"/schema_responses/{sid}/")["data"]["attributes"]
    ok = got["reviews_state"] == "approved" and got["revision_responses"][BLOCK].endswith(body)
    print(f"revision {sid}: {got['reviews_state']}; text {'in place' if ok else 'NOT FOUND'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
