from typing import Dict
from flask import Flask
from jwt import PyJWKClient
from .sso_utils import sso_utils
import re

class JwksManager():
    """
    Manage JWKS keys from different issuers, and caches the response
    """

    jwks_clients: Dict[str, PyJWKClient] = {}
    JWKS_CACHE_DURATION_SECONDS: int
    JWKS_URL: str

    def init_app(self, app: Flask):
        self.JWKS_CACHE_DURATION_SECONDS = app.config.get("JWKS_CACHE_DURATION_SECONDS")
        self.JWKS_URL = app.config.get("JWKS_URL")

    def __get_jwks_client(self, issuer: str) -> PyJWKClient:
        realm_name = sso_utils.get_realm_name(issuer)
        if realm_name not in self.jwks_clients:
            jwks_url = self.__get_jwks_url(realm_name)
            self.jwks_clients[realm_name] = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=self.JWKS_CACHE_DURATION_SECONDS)
        return self.jwks_clients[realm_name]

    def get_jwk(self, kid: str, issuer: str):
        jwks_client = self.__get_jwks_client(issuer)
        signing_key = jwks_client.get_signing_key(kid)
        return signing_key.key

    def __get_jwks_url(self, realm_name: str) -> str:
        return sso_utils.replace_realm_name(self.JWKS_URL, realm_name)

