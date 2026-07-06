from dataclasses import dataclass

from flask import current_app
from flask_mail import Message

from extension import mail


@dataclass
class MailResult:
    sent: bool
    error: str = ""

    def __bool__(self):
        return self.sent


def _configured_recipients(config_key):
    return [
        email.strip()
        for email in (current_app.config.get(config_key) or "").split(",")
        if email.strip()
    ]


def _attach_files(message, attachments):
    for attachment in attachments or []:
        if hasattr(attachment, "content_type"):
            message.attach(attachment)
            continue

        if not isinstance(attachment, tuple) or len(attachment) < 3:
            raise ValueError("Attachment must be an Attachment object or (filename, content_type, data)")

        filename, content_type, data = attachment[:3]
        disposition = attachment[3] if len(attachment) > 3 else None
        message.attach(
            filename=filename,
            content_type=content_type,
            data=data,
            disposition=disposition,
        )


def send_placement_mail(subject, recipients, body=None, html=None, attachments=None, recipient_group=None):
    clean_recipients = [email for email in (recipients or []) if email]

    if recipient_group == "student":
        routed_recipients = _configured_recipients("MAIL_STUDENT_RECIPIENTS")
    elif recipient_group == "staff":
        routed_recipients = _configured_recipients("MAIL_STAFF_RECIPIENTS")
    else:
        routed_recipients = []

    override_recipients = routed_recipients or _configured_recipients("MAIL_OVERRIDE_RECIPIENTS")
    if override_recipients:
        clean_recipients = override_recipients

    if not clean_recipients:
        error = "No recipient email found"
        current_app.logger.warning("Mail skipped for %s: %s", subject, error)
        return MailResult(False, error)

    username = (current_app.config.get("MAIL_USERNAME") or "").strip()
    password = (current_app.config.get("MAIL_PASSWORD") or "").strip()
    sender = (current_app.config.get("MAIL_DEFAULT_SENDER") or "").strip()

    if not sender:
        error = "MAIL_DEFAULT_SENDER is missing"
        current_app.logger.error("Mail skipped for %s: %s", subject, error)
        return MailResult(False, error)

    if not current_app.config.get("MAIL_SUPPRESS_SEND") and (not username or not password):
        error = "MAIL_USERNAME or MAIL_PASSWORD missing"
        current_app.logger.error(
            "Mail skipped for %s: %s",
            subject,
            error,
        )
        return MailResult(False, error)

    try:
        message = Message(
            subject=subject,
            sender=sender,
            recipients=clean_recipients,
            body=body,
            html=html,
        )
        _attach_files(message, attachments)
        mail.send(message)
        current_app.logger.info("Mail sent: %s -> %s", subject, ", ".join(clean_recipients))
        return MailResult(True)
    except Exception as exc:
        error = str(exc)
        current_app.logger.error(
            "Mail failed: %s -> %s: %s",
            subject,
            ", ".join(clean_recipients),
            exc,
            exc_info=True,
        )
        return MailResult(False, error)
