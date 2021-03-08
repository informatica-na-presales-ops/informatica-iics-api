import requests
import logging

log = logging.getLogger(__name__)


class APIClient:
    _base_api_url = None
    _session = requests.Session()
    _session_id = None

    def __init__(self, pod_region, username, password):
        self.login_url = f'https://dm-{pod_region}.informaticacloud.com/saas/public/core/v3/login'
        self.username = username
        self.password = password

    @property
    def base_api_url(self) -> str:
        if self._base_api_url is None:
            self.login()
        return self._base_api_url

    def get_agent_details(self):
        url = f'{self.base_api_url}/api/v2/agent/details'
        response = self._session.get(url)
        response.raise_for_status()
        data = response.json()
        return data

    def get_agents(self):
        url = f'{self.base_api_url}/api/v2/agent'
        response = self._session.get(url)
        response.raise_for_status()
        data = response.json()
        return data

    def get_security_log(self):
        url = f'{self.base_api_url}/public/core/v3/securityLog?limit=1000'
        response = self._session.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('entries')

    def login(self):
        log.debug('Attempting login...')
        json = {
            'username': self.username,
            'password': self.password
        }
        response = self._session.post(self.login_url, json=json)
        response.raise_for_status()
        data = response.json()
        self._base_api_url = data.get('products')[0].get('baseApiUrl')
        self._session_id = data.get('userInfo').get('sessionId')
        self._session.headers.update({
            'icSessionId': self._session_id,
            'INFA-SESSION-ID': self._session_id
        })
