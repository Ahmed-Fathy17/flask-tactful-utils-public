from typing import Dict
from flask import current_app, jsonify, request
from flask_jwt_extended import JWTManager , get_jwt_identity ,jwt_required
from .jwt_payload import JWTPayload
from functools import wraps

class TactfulJwt():
    jwt = JWTManager()
    def __init__(self,app):
        self.jwt.init_app(app)
    
    @staticmethod
    def get_jwt_identity()->JWTPayload:
        return get_jwt_identity()

    @staticmethod
    def jwt_required(func):
        @wraps(func)
        @jwt_required()
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper

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
        resp = current_app.make_response((jsonify({'error':{'type':'tokenExpired', 'msg':"Token has expired"}}), 401))
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
    def get_token_decoding_secret(unverified_headers: Dict,unverified_claims: Dict):
        audiance_secret_name = TactfulJwt.get_key_name_for_audiance(unverified_claims.get('sub').get('aud'))
        if audiance_secret_name is not None:
            return current_app.config.get(audiance_secret_name)
        # Support old tokens
        return current_app.config.get('JWT_SECRET_KEY')