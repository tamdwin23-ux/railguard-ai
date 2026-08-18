import json
from datetime import datetime, timezone

import boto3


BUCKET_NAME = "cloudlab-api-data-443920089735-eu-north-1-an"

s3 = boto3.client("s3")


def save_prediction(timestamp, payload):
    safe_timestamp = str(timestamp).replace(":", "-").replace(" ", "T")

    key = (
        f"railguard/predictions/"
        f"{safe_timestamp}.json"
    )

    body = {
        "stored_at": datetime.now(timezone.utc).isoformat(),
        "timestamp": timestamp,
        "data": payload,
    }

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(body).encode("utf-8"),
        ContentType="application/json",
    )

    return {
        "bucket": BUCKET_NAME,
        "key": key,
    }


def save_sensor_reading(timestamp, sensor_data):
    safe_timestamp = str(timestamp).replace(":", "-").replace(" ", "T")

    key = (
        f"railguard/raw-sensor-data/"
        f"{safe_timestamp}.json"
    )

    body = {
        "stored_at": datetime.now(timezone.utc).isoformat(),
        "timestamp": timestamp,
        "sensors": sensor_data,
    }

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(body).encode("utf-8"),
        ContentType="application/json",
    )

    return {
        "bucket": BUCKET_NAME,
        "key": key,
    }


def save_drift_event(timestamp, drift_data):
    safe_timestamp = str(timestamp).replace(":", "-").replace(" ", "T")

    key = (
        f"railguard/drift-events/"
        f"{safe_timestamp}.json"
    )

    body = {
        "stored_at": datetime.now(timezone.utc).isoformat(),
        "timestamp": timestamp,
        "drift": drift_data,
    }

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(body).encode("utf-8"),
        ContentType="application/json",
    )

    return {
        "bucket": BUCKET_NAME,
        "key": key,
    }


def save_drift_event(timestamp, drift_data):
    safe_timestamp = str(timestamp).replace(":", "-").replace(" ", "T")

    key = (
        f"railguard/drift-events/"
        f"{safe_timestamp}.json"
    )

    body = {
        "stored_at": datetime.now(timezone.utc).isoformat(),
        "timestamp": timestamp,
        "drift": drift_data,
    }

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=json.dumps(body).encode("utf-8"),
        ContentType="application/json",
    )

    return {
        "bucket": BUCKET_NAME,
        "key": key,
    }
