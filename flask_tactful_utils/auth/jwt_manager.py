
from flask_jwt_extended import JWTManager


jwt = JWTManager(app)


@jwt.user_loader_callback_loader
def user_loader_callback(identity):
    db_user = db.session.query(User).get(int(identity.get("id")))
    if db_user and db_user.is_active:
        return identity
    return None

@jwt.expired_token_loader
def user_token_expired(data=None):
    current_app.logger.debug("jwt.expired_token_loader callBack.......  ", data)
    resp = current_app.make_response((jsonify({'error':{'type':'tokenExpired', 'msg':"Token has expired"}}), 401))
    resp.headers['Access-Control-Allow-Origin'] = request.environ.get('HTTP_ORIGIN', '*')
    return resp

@jwt.encode_key_loader
def get_token_encoding_secret(identity):
    aud_secret = TOKEN_AUD.get(identity.get('aud')) 
    if aud_secret is not None:
        return aud_secret
    # Support old tokens
    # Swap to None to remove old token support
    return app_config.get('JWT_SECRET_KEY')

@jwt.decode_key_loader
def get_token_decoding_secret(unverified_claims, unverified_headers):
    aud_secret = TOKEN_AUD.get(unverified_claims.get('identity').get('aud'))
    if aud_secret is not None:
        return aud_secret
    # Support old tokens
    # Swap to None to remove old token support
    return app_config.get('JWT_SECRET_KEY')