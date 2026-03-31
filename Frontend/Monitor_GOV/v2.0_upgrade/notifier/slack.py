import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SlackNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_message(self, text: str, attachments: Optional[list] = None) -> bool:
        if not self.webhook_url:
            return False
        
        payload = {"text": text}
        if attachments:
            payload["attachments"] = attachments

        try:
            resp = requests.post(self.webhook_url, json=payload, timeout=10)
            resp.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False

    def send_notice(self, item: Dict[str, Any]):
        title = item.get("title", "No Title")
        link = item.get("link", "")
        score = item.get("score", 0)
        reasons = ", ".join(item.get("reasons", []))
        
        text = f"🚨 *[New High Score Notice]* ({score}pts)\n*<{link}|{title}>*\nReasons: {reasons}"
        return self.send_message(text)
