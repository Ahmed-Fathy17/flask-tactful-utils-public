# -*- coding: utf-8 -*-
from datetime import datetime


from flask import _request_ctx_stack, current_app, request, session, has_request_context, make_response # type: ignore

from werkzeug.local import LocalProxy

from flask_login import (LoginManager, SESSION_KEYS, _user_context_processor, 
decode_cookie, COOKIE_DURATION, COOKIE_HTTPONLY, COOKIE_SECURE, encode_cookie, _create_identifier, COOKIE_NAME,
_signals, user_logged_in, user_logged_out)

SESSION_KEYS.add('profile_id')

COOKIE_PROFILE_NAME = 'current_profile'

current_profile = LocalProxy(lambda: _get_profile()) # pylint: disable=W0108

current_user = LocalProxy(lambda: _get_user()) # pylint: disable=W0108

class TactfulLoginManager(LoginManager):
    '''
    This object is used to hold the settings used for logging in. Instances of
    :class:`LoginManager` are *not* bound to specific apps, so you can create
    one in the main body of your code and then bind it to your
    app in a factory function.
    '''
    def __init__(self, app=None, add_context_processor=True):
        super(TactfulLoginManager, self).__init__(app, add_context_processor)
        self.profile_callback = None
        self.role = None

    def init_app(self, app, add_context_processor=True):
        '''
        Configures an application. This registers an `after_request` call, and
        attaches this `LoginManager` to it as `app.login_manager`.

        :param app: The :class:`flask.Flask` object to configure.
        :type app: :class:`flask.Flask`
        :param add_context_processor: Whether to add a context processor to
            the app that adds a `current_user` variable to the template.
            Defaults to ``True``.
        :type add_context_processor: bool
        '''
        app.login_manager = self
        app.after_request(self._update_remember_cookie)

        self._login_disabled = app.config.get('LOGIN_DISABLED', False)

        if add_context_processor:
            app.context_processor(_user_context_processor)
            # app.context_processor(_profile_context_processor)
            
    def reload_user(self, user=None):
        ctx = _request_ctx_stack.top

        if user is None:
            user_id = session.get('user_id')
            if user_id is None:
                self.role = None
                ctx.user = self.anonymous_user()
            else:
                if self.user_callback is None:
                    raise Exception(
                        "No user_loader has been installed for this "
                        "LoginManager. Add one with the "
                        "'LoginManager.user_loader' decorator.")
                user = self.user_callback(user_id)
                if user is None:
                    self.role = None
                    ctx.user = self.anonymous_user()
                else:
                    ctx.user = user
        else:
            ctx.user = user

    def _update_remember_cookie(self, response):
        # Don't modify the session unless there's something to do.
        if 'remember' in session:
            operation = session.pop('remember', None)

            if operation == 'set' and 'user_id' in session:
                self._set_cookie(response)
                if 'profile_id' in session:
                    self._set_my_cookie(response, 'PROFILE_NAME', COOKIE_PROFILE_NAME)

            elif operation == 'clear':
                self._clear_cookie(response)
                self._clear_my_cookie(response, 'PROFILE_NAME', COOKIE_PROFILE_NAME)

        return response


    def _update_profile_cookie(self, response):        
        if 'profile_id' in session:
            self._set_my_cookie(response, 'PROFILE_NAME', COOKIE_PROFILE_NAME)

        return response


    def profile_loader(self, callback):
        self.profile_callback = callback
        return callback

    def _load_profile(self):
        config = current_app.config
        is_missing_profile_id = 'profile_id' not in session
        if is_missing_profile_id:
            cookie_name = config.get('PROFILE_NAME', COOKIE_PROFILE_NAME)
            has_cookie = (cookie_name in request.cookies)
            if has_cookie:
                return self._load_profile_from_cookie(request.cookies[cookie_name])
            else:
                return self.set_default_profile()

        return self.reload_profile()        

    def reload_profile(self, profile=None):
        ctx = _request_ctx_stack.top

        if profile is None:
            profile_id = session.get('profile_id')
            user_id = session.get('user_id')
            if profile_id is None:
                ctx.current_profile = None
            if user_id:
                self.role = current_user.role
                profile = self.profile_callback(user_id, profile_id, self.role)
                if profile is not None:
                    ctx.current_profile = profile
        else:
            ctx.current_profile = profile

    def _load_profile_from_cookie(self, cookie):
        profile_id = decode_cookie(cookie)
        if profile_id is not None:
            session['profile_id'] = profile_id
        self.reload_profile()

       
    def _set_my_cookie(self, response, section, item):
        # cookie settings
        config = current_app.config
        cookie_name = config.get(section, item)
        duration = config.get('REMEMBER_COOKIE_DURATION', COOKIE_DURATION)
        domain = config.get('REMEMBER_COOKIE_DOMAIN')
        path = config.get('REMEMBER_COOKIE_PATH', '/')
        secure = config.get('REMEMBER_COOKIE_SECURE', COOKIE_SECURE)
        httponly = config.get('REMEMBER_COOKIE_HTTPONLY', COOKIE_HTTPONLY)

        data = encode_cookie(str(session['profile_id']))
        expires = datetime.utcnow() + duration

        # actually set it
        response.set_cookie(cookie_name,
                            value=data,
                            expires=expires,
                            domain=domain,
                            path=path,
                            secure=secure,
                            httponly=httponly)

    def _clear_my_cookie(self, response, section, item):
        config = current_app.config
        cookie_name = config.get(section, item)
        domain = config.get('REMEMBER_COOKIE_DOMAIN')
        path = config.get('REMEMBER_COOKIE_PATH', '/')
        response.delete_cookie(cookie_name, domain=domain, path=path)

    def set_default_profile(self):
        user_id = session.get('user_id')
        if user_id:
            profile_id = default_profile_select(user_id)
            if not profile_id is None:
                session['profile_id'] = profile_id
                    
            current_app.login_manager.role = current_user.role
            profile = current_profile #pylint: disable=W0612
            self.reload_profile()

def login_user(user, remember=False, force=False, fresh=True):
    if not force and not user.is_active:
        return False

    user_id = getattr(user, current_app.login_manager.id_attribute)()
    session['user_id'] = user_id
    session['_fresh'] = fresh
    session['_id'] = _create_identifier()
    # profile_id = default_profile_select(user_id)
    # if not profile_id is None:
    #     session['profile_id'] = profile_id
    if remember:
        session['remember'] = 'set'

    _request_ctx_stack.top.user = user
    user_logged_in.send(current_app._get_current_object(), user=_get_user()) # pylint: disable=W0212
    current_app.login_manager.role = current_user.role
    profile = current_profile #pylint: disable=W0612
    return True
    
def default_profile_select(user_id):
    profile = current_app.login_manager.profile_callback(user_id)
    if profile is None:
        return None
    return profile.id

def logout_user():
    '''
    Logs a user out. (You do not need to pass the actual user.) This will
    also clean up the remember me cookie if it exists.
    '''

    user = _get_user()

    if 'user_id' in session:
        session.pop('user_id')

    if 'profile_id' in session:
        session.pop('profile_id')

    if '_fresh' in session:
        session.pop('_fresh')

    cookie_name = current_app.config.get('REMEMBER_COOKIE_NAME', COOKIE_NAME)
    if cookie_name in request.cookies:
        session['remember'] = 'clear'
        
    current_app.login_manager.reload_profile()
    user_logged_out.send(current_app._get_current_object(), user=user) # pylint: disable=W0212   
    current_app.login_manager.reload_user()
    return True

def _get_user():
    if has_request_context() and not hasattr(_request_ctx_stack.top, 'user'):
        current_app.login_manager._load_user() # pylint: disable=W0212
    user = getattr(_request_ctx_stack.top, 'user', None)
    return user 

def _get_profile():
    if has_request_context() and not hasattr(_request_ctx_stack.top, 'current_profile'):
        current_app.login_manager._load_profile() # pylint: disable=W0212
    profile = getattr(_request_ctx_stack.top, 'current_profile', None)
    return profile

def _profile_context_processor():
    return dict(current_profile=_get_profile())

def switch_profile(profile_id):
    session['profile_id'] = profile_id
    profile = current_profile #pylint: disable=W0612
    resp = make_response('', 200)
    current_app.login_manager._update_profile_cookie(resp) # pylint: disable=W0212

# Signals

profile_loaded_from_cookie = _signals.signal('loaded-from-cookie')
profile_loaded_from_request = _signals.signal('loaded-from-request')
