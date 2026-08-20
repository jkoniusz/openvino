# Copyright (C) 2018-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Post an NPU CiP bump notification as an Adaptive Card to a Microsoft Teams webhook.

Used by the "Send Teams notification" step of the NPU CiP Bump Notification workflow
(.github/workflows/npu_cip_bump_notification.yml). Follows the Adaptive Card / incoming
webhook approach of .github/scripts/agentic-workflows/notify_teams.py, but targets a
Power Automate ("Send webhook alerts to a channel") endpoint, which expects the bare
card. All content is passed via environment variables; the destination channel is
whichever channel owns the webhook in TEAMS_WEBHOOK_URL.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def main() -> None:
    webhook_url = os.environ.get("TEAMS_WEBHOOK_URL", "")
    if not webhook_url:
        print("TEAMS_WEBHOOK_URL not set; skipping Teams notification.")
        return

    facts = [
        {"title": "Date", "value": os.environ.get("CARD_DATE", "")},
        {"title": "Branch", "value": os.environ.get("CARD_BRANCH", "")},
        {"title": "Repository", "value": os.environ.get("CARD_REPO", "")},
    ]
    if os.environ.get("CARD_AUTHOR"):
        facts.append({"title": "Author", "value": os.environ["CARD_AUTHOR"]})
    if os.environ.get("CARD_PR_INFO"):
        facts.append({"title": "PR", "value": os.environ["CARD_PR_INFO"]})

    body = [
        {"type": "TextBlock", "text": "\U0001f514 NPU CiP bump detected",
         "weight": "Bolder", "size": "Medium", "color": "Attention", "wrap": True},
        {"type": "FactSet", "facts": facts},
        {"type": "TextBlock", "text": os.environ.get("CARD_CHANGES", ""),
         "wrap": True, "spacing": "Medium", "fontType": "Monospace"},
    ]

    commit_url = os.environ.get("CARD_COMMIT_URL", "")
    actions = [{"type": "Action.OpenUrl", "title": "View commit", "url": commit_url}] if commit_url else []

    # Power Automate ("Send webhook alerts to a channel") posts the request body directly
    # as an Adaptive Card, so send the bare card rather than the classic connector's
    # {"type": "message", "attachments": [...]} envelope, which renders as an empty message.
    payload = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body,
        "actions": actions,
    }

    request = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            print(f"Teams webhook responded with HTTP {response.status}")
    except urllib.error.HTTPError as error:
        sys.exit(f"Teams webhook failed with HTTP {error.code}: {error.read().decode('utf-8', 'replace')}")


if __name__ == "__main__":
    main()
