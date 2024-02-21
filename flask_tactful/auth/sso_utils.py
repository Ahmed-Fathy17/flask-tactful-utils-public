from keycloak import KeycloakAdmin
from typing import Optional
import os
import re
import requests


class SSOUtils:
    REALM_REGEX_PATTERN = r'/realms/([\w-]+)'
    client_secrets: dict = {}

    def __init__(self):
        self.keycloak_admin = KeycloakAdmin(
            server_url=os.environ.get('KEYCLOAK_HOST_URL'),
            username=os.environ.get('KEYCLOAK_ADMIN_USERNAME'),
            password=os.environ.get('KEYCLOAK_ADMIN_PASSWORD'),
        )

    def _init_client_secret(self, client_id: str):
        for realm in self.keycloak_admin.get_realms():
            realm_name = realm['realm']
            self.keycloak_admin.change_current_realm(realm_name)
            client = {c['clientId']: c['secret'] for c in self.keycloak_admin.get_clients() if c['clientId'] == client_id}
            self.client_secrets[realm_name] = client

    def get_client_secret(self, client_id: str, *, realm_name: str = None, issuer_url: str = None):
        if realm_name is None:
            realm_name = self.get_realm_name(issuer_url)
        if realm_name not in self.client_secrets or client_id not in self.client_secrets[realm_name]:
            self._init_client_secret(client_id)
        return self.client_secrets[realm_name][client_id]

    def get_realm_name(self, url: str) -> Optional[str]:
        try:
            return re.search(self.REALM_REGEX_PATTERN, url).groups()[0]
        except:
            return os.environ.get('SSO_DEFAULT_REALM')

    def replace_realm_name(self, url: str, realm_name: str) -> str:
        if realm_name:
            return re.sub(self.REALM_REGEX_PATTERN, f'/realms/{realm_name}', url)
        return url

    def get_certificates(self) -> dict:
        jwks_certicates: dict = {'keys': []}

        for realm in self.keycloak_admin.get_realms():
            realm_name = realm['realm']
            jwks_url = f'{self.keycloak_admin.server_url}/realms/{realm_name}/protocol/openid-connect/certs'
            req = requests.get(jwks_url)
            if req.ok:
                jwks_certicates['keys'] += req.json()['keys']

        return jwks_certicates


sso_utils = SSOUtils()
