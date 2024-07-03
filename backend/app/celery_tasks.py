from flask import current_app, render_template
from app import db
from flask_mail import Message
from . import mail


celery = current_app.celery


@celery.task(name='app.send_email', bind=True)
def send_email(self, recipients, subject, template, **kwargs):
    msg = Message(current_app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=current_app.config['MAIL_SENDER'], recipients=recipients)
    msg.html = render_template(template, **kwargs)
    try:
        mail.send(msg)
    except Exception as e:
        self.retry(exc=e)


@celery.task(name='app.reverse', bind=True)
def reverse(self, string):
    d = dict()
    try:
        d['msg'] = string[::-1]
    except Exception as e:
        d['msg'] = str(e)
        d['success'] = False
    else:
        d['success'] = True
    return d
