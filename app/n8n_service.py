import json
import urllib.request


N8N_MAINTENANCE_WEBHOOK = (
    "https://n8n.edwinaisolution.com/"
    "webhook/railguard-maintenance"
)


def send_maintenance_event(event):
    payload = json.dumps({
        "event": event
    }).encode("utf-8")

    request = urllib.request.Request(
        N8N_MAINTENANCE_WEBHOOK,
        data=payload,
        headers={
            "Content-Type": "application/json"
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
