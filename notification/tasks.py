import smtplib
from typing import List, Dict
from celery import shared_task
from notification.utils import EmailManager


@shared_task(
    bind=True,
    autoretry_for=(smtplib.SMTPException,),
)
def send_mail_async(
    self, template: str, recipients: List[str], subject: str, context: Dict
):
    mail = EmailManager(
        template=template,
        recipients=recipients,
        subject=subject,
        context=context,
    )
    mail.send()
