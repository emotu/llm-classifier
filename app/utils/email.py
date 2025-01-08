"""
email.py

@author: Emotu Balogun
@created: December 14, 2024

Email notification service for sending automated emails to users.

This module handles email notifications and communications sent by the application.
It provides functionality for composing and sending emails using configurable
email templates.

Key Features:
    - Templated email notifications
    - Support for HTML and plain text emails

Usage:
    The email service is used by other application components to send
    notifications and communications to users.

Example:
    >>> from app.services.email import EmailService
    >>> email_service = EmailService()
    >>> await email_service.send_welcome_email(user_email="user@example.com")

Notes:
    - Requires email service credentials to be configured in settings
    - Templates should be stored in the templates directory
"""

import resend
from jinja2 import Environment, PackageLoader, select_autoescape

from app.config import settings

resend.api_key = settings.RESEND_API_KEY

default_context = {
    "app_name": settings.API_NAME,
    "app_url": settings.BASE_URL,
    "app_logo_url": settings.APP_LOGO,
}

env = Environment(
    loader=PackageLoader("app", "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)


def determin_target_email(to: str) -> str:
    if settings.ALLOW_EMAIL == "dev_only" and to != settings.DEV_EMAIL:
        return settings.DEV_EMAIL
    return to


async def send_email(
    template_name: str,
    to: str,
    subject: str,
    context: dict = {},
    attachments: list[resend.Attachment] = [],
):
    context = {**default_context, **context}

    template = env.get_template(template_name)
    html = template.render(context)

    recipients = determin_target_email(to).split(",")

    if not settings.ALLOW_EMAIL or settings.ALLOW_EMAIL == "off":
        print(
            f"Email not sent to {recipients} because ALLOW_EMAIL is {settings.ALLOW_EMAIL}"
        )
        return

    params: resend.Emails.SendParams = {
        "from": settings.RESEND_FROM_EMAIL,
        "to": recipients,
        "subject": subject,
        "html": html,
        "attachments": attachments,
    }
    status = resend.Emails.send(params)

    return status
