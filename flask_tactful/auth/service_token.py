from datetime import datetime
import requests
from .jwt_payload import OauthCreds,ServiceAccessToken
from .sso_utils import sso_utils
import math

class ServiceToken:
  def __init__(self,oauth_creds: dict):
    self.oauth_creds = OauthCreds(
      client_id=oauth_creds.get('client_id'),
      client_secret=sso_utils.get_client_secret(oauth_creds.get('client_id')),
      token_endpoint=oauth_creds.get('token_endpoint')
    )
    self._token = ServiceAccessToken("",0)

  def get_token(self):
      
    if not self.is_token_valid():
        return self._reset_token()
    
    return self._token.access_token


  def _calculate_expiration_time(self,expires_in_seconds: int):
      current_time  = datetime.now()

      expiration_time = int(current_time.timestamp()) + expires_in_seconds * 1000
      return math.floor(expiration_time / 1000)
  
  def is_token_valid(self):
    current_time_in_seconds = int(datetime.now().timestamp())/1000 
    return current_time_in_seconds < self._token.expires_in  if self._token else False

  def _reset_token(self):
    try:
          
      data = {
        "client_id": self.oauth_creds.client_id,
        "client_secret": self.oauth_creds.client_secret,
        "grant_type": 'client_credentials',
      }
      headers =  {
          'Content-Type': 'application/x-www-form-urlencoded',
        }

      response = requests.post(url=self.oauth_creds.token_endpoint+'?role=admin', data=data, headers=headers)  
      token_data =  response.json()
      self._token = ServiceAccessToken(access_token = token_data.get("access_token"), expires_in= self._calculate_expiration_time(token_data.get("expires_in")))
      return self._token.access_token
                            
    except requests.exceptions.HTTPError as e:
      raise e
    except Exception as e:
      raise e

