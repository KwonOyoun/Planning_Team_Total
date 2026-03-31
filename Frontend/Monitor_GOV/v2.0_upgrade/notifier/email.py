import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class EmailNotifier:
    def __init__(self, server: str, port: int, user: str, password: str, recipients: List[str]):
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.recipients = recipients

    def send_email(self, subject: str, body: str) -> bool:
        if not self.recipients or not self.user:
            return False

        msg = MIMEMultipart()
        msg["From"] = self.user
        msg["To"] = ", ".join(self.recipients)
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "html"))

        try:
            with smtplib.SMTP(self.server, self.port) as s:
                s.starttls()
                s.login(self.user, self.password)
                s.send_message(msg)
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_notice(self, item: Dict[str, Any]):
        title = item.get("title", "No Title")
        link = item.get("link", "#")
        score = item.get("score", 0)
        reasons = "<br>".join([f"- {r}" for r in item.get("reasons", [])])
        
        subject = f"[GovMonitor] High Score Notice: {title} ({score}pts)"
        body = f"""
        <h2><a href="{link}">{title}</a></h2>
        <p><b>Score:</b> {score}</p>
        <p><b>Reasons:</b></p>
        <blockquote>{reasons}</blockquote>
        <p><b>Source:</b> {item.get('source')}</p>
        <p><b>Institution:</b> {item.get('institution')}</p>
        """
        return self.send_email(subject, body)
