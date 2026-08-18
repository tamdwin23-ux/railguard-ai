import json
import os
import urllib.request


def send_maintenance_event(event):
    webhook_url = os.getenv("N8N_MAINTENANCE_WEBHOOK")
    webhook_token = os.getenv("N8N_WEBHOOK_TOKEN")

    if not webhook_url:
        raise RuntimeError(
            "N8N_MAINTENANCE_WEBHOOK is not configured"
        )

    if not webhook_token:
        raise RuntimeError(
            "N8N_WEBHOOK_TOKEN is not configured"
        )

    payload = json.dumps({
        "event": event
    }).encode("utf-8")

    request = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-RailGuard-Token": webhook_token,
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=15,
    ) as response:
        return {
            "status_code": response.status,
            "sent": True,
        }
