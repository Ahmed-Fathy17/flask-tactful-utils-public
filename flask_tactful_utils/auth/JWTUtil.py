from datetime import timedelta, datetime
from flask import current_app as app
from flask_jwt_extended import create_access_token, create_refresh_token
from app.app_creator import db
from app.authentication.jwtPayload import JWTAccessPayload, JWTCredintial, JWTPayload
from app.errors import ItemNotExistsException
from app.models import Sessions, User
from app.services import ProfileService

def create_user_profile_jwt_payload(user:User, profile_name:str=None,audience:str='dash', ignore_id:bool=False, custom_role:str=None,expire_access:timedelta=None, expire_refresh:timedelta=None):
    jwt_refresh_payload = JWTPayload(email = user.email, aud=audience, role=user.role)
    jwt_access_payload = JWTAccessPayload(email=user.email, aud=audience, role= user.role)

    if not expire_access:
        expire_access = timedelta(days=1)
    if not expire_refresh:
        expire_refresh = timedelta(days=31)
    
    exp_refresh_date = datetime.now() + expire_refresh
    jwt_access_payload.expires_on = exp_refresh_date
    jwt_refresh_payload.expires_on = exp_refresh_date
    
    if not ignore_id:
        jwt_access_payload.id = user.id
        jwt_refresh_payload.id = user.id
    

    if profile_name is not None:
        set_profile_jwt_payload(jwt_access_payload,user, profile_name, custom_role)
    
    return jwt_access_payload, jwt_refresh_payload

def set_profile_jwt_payload(jwt_access_payload:JWTAccessPayload,user:User, profile_name:str,custom_role:str):
    profile = ProfileService.get_profile_by_name(profile_name)
    
    if profile is None:
        return 
    try:
        user_role = ProfileService.get_user_profile_role(profile.id, user.id)
        if custom_role is None:
            jwt_access_payload.profile_role = user_role.get('role')  
        else:
            jwt_access_payload.profile_role = custom_role 
        
    except ItemNotExistsException:
        app.logger.info(f"No relation between current user and profile {profile.name}.")

    jwt_access_payload.profile_name = profile.name    
    
    
    jwt_access_payload.profile_id = profile.id
    
    


def create_jwt_token(jwt_access_payload:JWTAccessPayload = None, jwt_refresh_payload:JWTPayload = None,fresh:bool=True, create_refresh:bool=True, expire_access:timedelta=None, expire_refresh:timedelta=None):
    jwt_credintial = JWTCredintial()
    
    jwt_credintial.user_access_token = create_access_token(identity=jwt_access_payload.__dict__, expires_delta=expire_access, fresh=fresh)
    
    if create_refresh is True:
        jwt_credintial.user_refresh_token = create_refresh_token(identity=jwt_refresh_payload.__dict__, expires_delta=expire_refresh)
    return jwt_credintial

def add_session_object(jwt_credintial:JWTCredintial,user:User, jwt_refresh_payload:JWTPayload, request_ip:str=None):
    session = Sessions()
    session.user = user
    session.expires_on = jwt_refresh_payload.expires_on
    session.audience = jwt_refresh_payload.aud
    session.token = jwt_credintial.user_refresh_token
    session.ip = request_ip
    db.session.add(session)
    db.session.commit()
    return session


def create_JWTToken(user:User=None, profile_name:str=None, audience:str='dash', ignore_id:bool = False, custom_role:str = None, expire_access:timedelta=None, expire_refresh:timedelta=None,request_ip:str=None, fresh:bool=True, create_refresh:bool=True):
    jwt_access_payload, jwt_refresh_payload = create_user_profile_jwt_payload(user,profile_name, audience,ignore_id,custom_role,expire_access,expire_refresh)
    jwt_credintial = create_jwt_token(jwt_access_payload, jwt_refresh_payload,fresh,create_refresh,expire_access,expire_refresh)
    return  jwt_access_payload , jwt_credintial


def set_external_profile_jwt_payload(jwt_access_payload:JWTAccessPayload,user:User, profile_name:str, custom_role:str=None):
    
    profile = ProfileService.get_profile_by_name(profile_name)

    if profile is None:
        return 
    
    try:
        user_role = ProfileService.get_user_profile_role(profile.id, user.id)
    except ItemNotExistsException:
        app.logger.info(f"No relation between current user and profile {profile.name}.")

    jwt_access_payload.profile_name = profile.name    
    if custom_role is None:
        jwt_access_payload.profile_role = user_role.get('role') if user_role.get('role') !="admin" else "manager"
    else:
        jwt_access_payload.profile_role = custom_role
    jwt_access_payload.profile_id = profile.id



def create_user_profile_external_jwt_payload(user:User, profile_name:str=None, ignore_id:bool=False, custom_role:str=None):
    jwt_access_payload = JWTAccessPayload(email = user.email, role = user.role)
    
    if not ignore_id:
        jwt_access_payload.id = user.id

    if profile_name is not None:
        set_external_profile_jwt_payload(jwt_access_payload,user, profile_name, custom_role)
    
    return jwt_access_payload



def creat_external_JWTToken( user:User, profile_name:str=None, ignore_id:bool=False, custom_role:str=None,
                            expire_access:timedelta=None, audience:str='dash', create_refresh:bool=True):
    jwt_access_payload = create_user_profile_external_jwt_payload(user,profile_name,ignore_id, custom_role)
    jwt_credintial = create_jwt_token(jwt_access_payload = jwt_access_payload, expire_access= expire_access,create_refresh=create_refresh )
    return jwt_access_payload, jwt_credintial