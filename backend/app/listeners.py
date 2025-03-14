from sqlalchemy import event
from sqlalchemy.orm import Session
from .models import User, Role, WebAuthnCredential
import datetime
import uuid


def user_before_insert(mapper, connection, target):
    if target.alternative_id is None:
        target.alternative_id = User.generate_alternative_id()
    if target.r2_uuid is None:
        target.r2_uuid = uuid.uuid4().hex


def user_before_flush(session, flush_context, instances):
    for instance in session.new:
        if isinstance(instance, User) and instance.role is None:
            instance.role = Role.query.filter_by(default=True).first()


def webauthn_before_insert(mapper, connection, target):
    if target.created_at is None:
        target.created_at = datetime.datetime.now()
    if target.name is None:
        target.name = f"New Authenticator {target.formatted_created_at}"


event.listen(User, 'before_insert', user_before_insert)
event.listen(Session, 'before_flush', user_before_flush)
event.listen(WebAuthnCredential, 'before_insert', webauthn_before_insert)
