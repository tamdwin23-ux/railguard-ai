from datetime import datetime
from app.model_service import CONFIG

FAULT_ANOMALY_MINUTES = CONFIG["risk_engine"]["fault_anomaly_minutes"]
GAP_TOLERANCE_MINUTES = CONFIG["risk_engine"]["gap_tolerance_minutes"]
WATCH_MINUTES = CONFIG["risk_engine"]["watch_minimum_minutes"]


class RuntimeRiskEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        self.global_anomaly_minutes = 0
        self.normal_gap_minutes = 0
        self.watch_minutes = 0
        self.watch_start = None
        self.watch_emitted = False
        self.fault_open = False
        self.incident_id = 0
        self.fault_start = None
        self.last_timestamp = None

    def process(self, timestamp, prediction):
        timestamp = datetime.fromisoformat(str(timestamp))

        global_anomaly = bool(prediction["global_anomaly"])
        regime_anomaly = bool(prediction["regime_anomaly"])
        event = None

        if self.last_timestamp is not None:
            gap_minutes = (
                timestamp - self.last_timestamp
            ).total_seconds() / 60

            if gap_minutes > 3:
                if not self.fault_open:
                    self.global_anomaly_minutes = 0
                    self.normal_gap_minutes = 0

                self.watch_minutes = 0
                self.watch_start = None
                self.watch_emitted = False

        if global_anomaly:
            self.normal_gap_minutes = 0

            if self.global_anomaly_minutes == 0:
                self.fault_start = timestamp

            self.global_anomaly_minutes += 1

            if (
                self.global_anomaly_minutes >= FAULT_ANOMALY_MINUTES
                and not self.fault_open
            ):
                self.incident_id += 1
                self.fault_open = True

                event = {
                    "event_type": "CONFIRMED_FAULT",
                    "risk_level": "CRITICAL",
                    "incident_id": self.incident_id,
                    "fault_start": self.fault_start.isoformat(),
                    "confirmed_at": timestamp.isoformat(),
                    "anomaly_minutes": self.global_anomaly_minutes,
                }

        else:
            if not self.fault_open and self.global_anomaly_minutes > 0:
                self.normal_gap_minutes += 1

                if self.normal_gap_minutes > GAP_TOLERANCE_MINUTES:
                    self.global_anomaly_minutes = 0
                    self.normal_gap_minutes = 0
                    self.fault_start = None

        watch_signal = (
            regime_anomaly
            and not global_anomaly
            and not self.fault_open
        )

        if watch_signal:
            if self.watch_minutes == 0:
                self.watch_start = timestamp

            self.watch_minutes += 1

            if (
                self.watch_minutes >= WATCH_MINUTES
                and not self.watch_emitted
            ):
                self.watch_emitted = True

                event = {
                    "event_type": "WATCH_EPISODE",
                    "risk_level": "WATCH",
                    "started_at": self.watch_start.isoformat(),
                    "detected_at": timestamp.isoformat(),
                    "watch_minutes": self.watch_minutes,
                }

        else:
            self.watch_minutes = 0
            self.watch_start = None
            self.watch_emitted = False

        self.last_timestamp = timestamp

        return {
            "event": event,
            "fault_open": self.fault_open,
            "incident_id": self.incident_id if self.fault_open else None,
            "global_anomaly_minutes": self.global_anomaly_minutes,
            "watch_minutes": self.watch_minutes,
        }

    def resolve_fault(self):
        if not self.fault_open:
            return None

        resolved_id = self.incident_id

        self.fault_open = False
        self.global_anomaly_minutes = 0
        self.normal_gap_minutes = 0
        self.fault_start = None

        return {
            "event_type": "FAULT_RESOLVED",
            "risk_level": "LOW",
            "incident_id": resolved_id,
        }


risk_engine = RuntimeRiskEngine()
