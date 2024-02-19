from keycloak import KeycloakAdmin
from urllib.parse import urlparse
from typing import Optional
import os
import re


class SSOUtils:
    REALM_REGEX_PATTERN = r'/realms/([\w-]+)'
    client_secrets: dict = {}

    def __init__(self):
        url = urlparse(os.environ.get('JWKS_URL'))

        self.keycloak_admin = KeycloakAdmin(
            server_url=f"{url.scheme}://{url.netloc}",
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
            issuer_url = issuer_url or os.environ.get('JWKS_URL')
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


sso_utils = SSOUtils()
