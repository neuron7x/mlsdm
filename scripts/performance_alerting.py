"""Automated performance alerting for production."""
from __future__ import annotations

import os
import time
from typing import Any

import requests


class PerformanceAlerter:
    """Alert on SLO violations."""

    def __init__(
        self,
        api_url: str,
        slack_webhook: str | None = None,
        email_api: str | None = None,
    ) -> None:
        self.api_url = api_url
        self.slack_webhook = slack_webhook
        self.email_api = email_api
        self._last_alert_time: dict[str, float] = {}

    def check_and_alert(self) -> None:
        """Check metrics and send alerts if needed."""
        try:
            response = requests.get(
                f"{self.api_url}/metrics/performance",
                timeout=10,
            )
            data: dict[str, Any] = response.json()

            if not data.get("slo_compliant", True):
                self._send_alerts(data.get("violations", []))

        except Exception as exc:
            print(f"Error checking metrics: {exc}")

    def _send_alerts(self, violations: list[str]) -> None:
        """Send alerts via configured channels."""
        alert_message = self._format_alert(violations)

        if self.slack_webhook:
            self._send_slack_alert(alert_message)

        if self.email_api:
            self._send_email_alert(alert_message)

        print(f"🚨 PERFORMANCE ALERT:\n{alert_message}")

    def _format_alert(self, violations: list[str]) -> str:
        """Format alert message."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

        message = f"⚠️ SLO Violations Detected at {timestamp}\n\n"
        for violation in violations:
            message += f"• {violation}\n"

        return message

    def _send_slack_alert(self, message: str) -> None:
        """Send Slack alert."""
        try:
            requests.post(
                self.slack_webhook,
                json={"text": message},
                timeout=10,
            )
        except Exception as exc:
            print(f"Failed to send Slack alert: {exc}")

    def _send_email_alert(self, message: str) -> None:
        """Send email alert."""
        try:
            requests.post(
                self.email_api,
                json={
                    "subject": "🚨 MLSDM Performance Alert",
                    "body": message,
                },
                timeout=10,
            )
        except Exception as exc:
            print(f"Failed to send email alert: {exc}")


def main() -> None:
    """Run continuous monitoring."""
    alerter = PerformanceAlerter(
        api_url="http://localhost:8000",
        slack_webhook=os.getenv("SLACK_WEBHOOK_URL"),
        email_api=os.getenv("EMAIL_API_URL"),
    )

    while True:
        alerter.check_and_alert()
        time.sleep(60)


if __name__ == "__main__":
    main()
