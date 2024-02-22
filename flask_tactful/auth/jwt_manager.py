import os
from typing import Dict, Optional
from jwt import PyJWKClient
from flask import current_app, jsonify, request
from flask_jwt_extended import JWTManager, jwt_required, current_user

from .jwks_manager import JwksManager
from .jwt_payload import JWTPayload
from .jwt_utils import get_jwt_identity
from functools import wraps

jwt_manager = JWTManager()
jwks_manager = JwksManager()


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
    
    jwt_manager: JWTManager

    def __init__(self, app):
        jwt_manager.init_app(app)
        self.jwt_manager = jwt_manager
        app.config.update(JWKS_CACHE_DURATION_SECONDS=int(os.environ.get("JWKS_CACHE_DURATION_SECONDS", 60 * 60)))
        jwks_manager.init_app(app)

    @staticmethod
    def get_jwt_identity() -> JWTPayload:
        return get_jwt_identity()

    @staticmethod
    def jwt_required(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def get_jwk(kid: str, issuer: str):
        try:
            return jwks_manager.get_jwk(kid, issuer)
        except Exception as e:
            current_app.logger.error(f"error getting jwk set {e}")

    # returns the key name, example "dash" -> "SECRET_KEY_DASH"
    @staticmethod
    def get_key_name_for_audiance(aud: str) -> str:
        if not aud:
            return "JWT_SECRET_KEY"
        return f"SECRET_KEY_{aud.upper()}"

@jwt_manager.user_lookup_loader
def user_lookup_loader(_jwt_header: Dict, jwt_payload: Dict):
    return jwt_payload

@jwt_manager.expired_token_loader
def user_token_expired(jwt_header, jwt_payload):
    current_app.logger.debug("jwt.expired_token_loader callBack.......  ", jwt_payload)
    resp = current_app.make_response((jsonify({'error': {'type': 'tokenExpired', 'msg': "Token has expired"}}), 401))
    resp.headers['Access-Control-Allow-Origin'] = request.environ.get('HTTP_ORIGIN', '*')
    return resp

@jwt_manager.encode_key_loader
def get_token_encoding_secret(identity: Dict):
    secret: str
    audiance_secret_name = TactfulJwt.get_key_name_for_audiance(identity.get('aud',None))
    if audiance_secret_name:
        secret = current_app.config[audiance_secret_name]
    else:
        # Support old tokens
        secret = current_app.config['JWT_SECRET_KEY']
    return secret

@jwt_manager.decode_key_loader
def get_token_decoding_secret(unverified_headers: Dict, unverified_claims: Dict):
    jwk = None
    secret: Optional[str] = None
    if unverified_headers.get('kid'):
        jwk = TactfulJwt.get_jwk(unverified_headers['kid'], unverified_claims['iss'])
    if jwk:
        current_app.logger.debug(f"returning jwk {jwk}")
        secret = jwk
    has_audience = 'aud' in unverified_claims.get('sub', {})
    if (not secret) and has_audience:
        audiance_secret_name = TactfulJwt.get_key_name_for_audiance(unverified_claims['sub']['aud'])
        current_app.logger.debug(f"returning secret for {audiance_secret_name}")
        if audiance_secret_name:
            secret = current_app.config.get(audiance_secret_name)
    # Support old tokens
    if not secret:
        current_app.logger.debug(f"returning original secret JWT_SECRET_KEY")
        secret = current_app.config['JWT_SECRET_KEY']
    return secret
