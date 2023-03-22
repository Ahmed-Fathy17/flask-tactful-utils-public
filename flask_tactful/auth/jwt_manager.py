import jwt
from typing import Dict
from jwt import PyJWKClient
from flask import current_app, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, current_user
from .jwt_payload import JWTPayload
from functools import wraps

jwt = JWTManager()

def get_current_user():
    if current_user and isinstance(current_user.get('sub'), str):
        return current_user
    return current_user.get('sub')


class TactfulJwt():
    """Extends JWTManager from flask_jwt_extended to enable features like:

     - accessing a JWKS (JSON Web Key Set) to support rotating keys 
     and decoding tokens without having to know the secret key
     - Supports multiple keys (one per audience)
     - Supports loading user data encoded in the JWT payload as current_user
    """

    def __init__(self, app):
        jwt.init_app(app)

    @staticmethod
    def get_jwt_identity() -> JWTPayload:
        jwt_user = get_current_user()
        payload = JWTPayload(id=jwt_user.get("id"), sub=jwt_user.get("sub"), email=jwt_user.get("email"), role=jwt_user.get("role"), aud=jwt_user.get("aud"))
        return payload

    @staticmethod
    def jwt_required(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def get_jwk(kid: str):
        try:
            jwks_url = current_app.config.get("JWKS_URL")
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key(kid)
            if signing_key and signing_key.key:
                return signing_key.key
        except Exception as e:
            print(e)

    # returns the key name, example "dash" -> "SECRET_KEY_DASH"
    @staticmethod
    def get_key_name_for_audiance(aud: str) -> str:
        if not aud:
            return None
        return f"SECRET_KEY_{aud.upper()}"

@jwt.user_lookup_loader
def user_lookup_loader(_jwt_header: Dict, jwt_payload: Dict):
    return jwt_payload

@jwt.expired_token_loader
def user_token_expired(jwt_header, jwt_payload):
    current_app.logger.debug("jwt.expired_token_loader callBack.......  ", jwt_payload)
    resp = current_app.make_response((jsonify({'error': {'type': 'tokenExpired', 'msg': "Token has expired"}}), 401))
    resp.headers['Access-Control-Allow-Origin'] = request.environ.get('HTTP_ORIGIN', '*')
    return resp

@jwt.encode_key_loader
def get_token_encoding_secret(identity: Dict):
    audiance_secret_name = TactfulJwt.get_key_name_for_audiance(identity.get('aud'))
    if audiance_secret_name is not None:
        return current_app.config.get(audiance_secret_name)
    else:
        # Support old tokens
        return current_app.config.get('JWT_SECRET_KEY')

@jwt.decode_key_loader
def get_token_decoding_secret(unverified_headers: Dict, unverified_claims: Dict):
    jwk = TactfulJwt.get_jwk(unverified_headers.get('kid'))
    if jwk:
        return jwk
    audiance_secret_name = TactfulJwt.get_key_name_for_audiance(unverified_claims.get('sub').get('aud'))
    if audiance_secret_name is not None:
        return current_app.config.get(audiance_secret_name)
    # Support old tokens
    return current_app.config.get('JWT_SECRET_KEY')
