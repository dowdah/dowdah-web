from flask import Blueprint, jsonify, request, current_app, g
from webauthn import generate_registration_options, generate_authentication_options, verify_registration_response, \
    verify_authentication_response
from webauthn.helpers import options_to_json, base64url_to_bytes
from webauthn.helpers.structs import PublicKeyCredentialDescriptor
from ...models import WebAuthnCredential
from ... import db
import json


webauthn_bp = Blueprint('webauthn', __name__)


@webauthn_bp.route('/my-authenticators', methods=['GET'])
def my_authenticators():
    user = g.current_user
    response_json = {
        'success': True,
        'code': 200,
        'authenticators': [credential.to_json() for credential in user.webauthn_credentials]
    }
    return jsonify(response_json), response_json['code']


@webauthn_bp.route('/register/begin', methods=['GET'])
def webauthn_register_begin():
    user = g.current_user
    rp_entity = {
        "id": current_app.config['DOMAIN'],
        "name": current_app.config['SITE_NAME']
    }
    user_entity = {
        "id": bytes(user.id),
        "name": user.username,
        "display_name": user.username
    }
    exclude_credentials = [PublicKeyCredentialDescriptor(id=base64url_to_bytes(credential.credential_id))
                           for credential in user.webauthn_credentials]
    options = generate_registration_options(rp_id=rp_entity["id"], rp_name=rp_entity["name"],
                                            user_id=user_entity["id"], user_name=user_entity["name"],
                                            user_display_name=user_entity["display_name"],
                                            exclude_credentials=exclude_credentials)
    response_json = {
        'success': True,
        'code': 200,
        'options': json.loads(options_to_json(options))
    }
    return jsonify(response_json), response_json['code']


@webauthn_bp.route('/register/complete', methods=['POST'])
def webauthn_register_complete():
    user = g.current_user
    request_json = request.json
    schema = "https://" if current_app.config['USE_SSL'] else "http://"
    try:
        registration_verification = verify_registration_response(
            credential=request_json,
            expected_rp_id=current_app.config['DOMAIN'],
            expected_origin=f"{schema}{current_app.config['DOMAIN']}",
            expected_challenge=base64url_to_bytes(request_json['challenge'])
        )
        credential = WebAuthnCredential(
            user_id=user.id,
            credential_id=request_json['id'],
            public_key=registration_verification.credential_public_key,
            sign_count=registration_verification.sign_count
        )
        db.session.add(credential)
        db.session.commit()
        response_json = {
            'success': True,
            'code': 200,
            'msg': 'Registration successful'
        }
    except Exception as e:
        db.session.rollback()
        response_json = {
            'success': False,
            'code': 400,
            'msg': f"Registration failed: {str(e)}"
        }
    return jsonify(response_json), response_json['code']


@webauthn_bp.route('/login/begin', methods=['GET'])
def webauthn_login_begin():
    options = generate_authentication_options(rp_id=current_app.config['DOMAIN'])
    response_json = {
        'success': True,
        'code': 200,
        'options': json.loads(options_to_json(options))
    }
    return jsonify(response_json), response_json['code']


@webauthn_bp.route('/login/complete', methods=['POST'])
def webauthn_login_complete():
    request_json = request.json
    credential = WebAuthnCredential.query.filter_by(credential_id=request_json['id']).first()
    schema = "https://" if current_app.config['USE_SSL'] else "http://"
    if credential is None:
        response_json = {
            'success': False,
            'code': 400,
            'msg': 'Credential not found'
        }
    else:
        try:
            authentication_verification = verify_authentication_response(
                credential=request_json,
                expected_rp_id=current_app.config['DOMAIN'],
                expected_origin=f"{schema}{current_app.config['DOMAIN']}",
                expected_challenge=base64url_to_bytes(request_json['challenge']),
                credential_public_key=credential.public_key,
                credential_current_sign_count=credential.sign_count
            )
            credential.sign_count = authentication_verification.new_sign_count
            user = credential.user
            db.session.add(credential)
            db.session.commit()
            response_json = {
                'success': True,
                'code': 200,
                'msg': 'Login successful',
                'access_token': user.generate_access_token(),
                'refresh_token': user.generate_refresh_token(),
                'user': user.to_json()
            }
        except Exception as e:
            db.session.rollback()
            response_json = {
                'success': False,
                'code': 400,
                'msg': f"Authentication failed: {str(e)}"
            }
    return jsonify(response_json), response_json['code']