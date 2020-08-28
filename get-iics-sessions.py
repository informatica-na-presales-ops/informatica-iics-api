import logging
import os
import requests
import signal
import sys

_version = '2020.0'

log = logging.getLogger(__name__)


class APIClient:
    _base_api_url = None
    _password = None
    _pod_region = None
    _session = requests.Session()
    _session_id = None
    _username = None

    @property
    def base_api_url(self) -> str:
        if self._base_api_url is None:
            self.login()
        return self._base_api_url

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
        self._session.headers.update({'INFA-SESSION-ID': self._session_id})

    @property
    def login_url(self) -> str:
        return f'https://dm-{self.pod_region}.informaticacloud.com/saas/public/core/v3/login'

    @property
    def password(self) -> str:
        if self._password is None:
            if 'IICS_PASSWORD' in os.environ:
                self._password = os.getenv('IICS_PASSWORD')
            else:
                raise RuntimeError('You must set the environment variable IICS_PASSWORD')
        return self._password

    @property
    def pod_region(self) -> str:
        if self._pod_region is None:
            self._pod_region = os.getenv('POD_REGION', 'us')
        return self._pod_region

    def get_security_log(self):
        url = f'{self.base_api_url}/public/core/v3/securityLog?limit=1000'
        response = self._session.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('entries')

    @property
    def username(self) -> str:
        if self._username is None:
            if 'IICS_USERNAME' in os.environ:
                self._username = os.getenv('IICS_USERNAME')
            else:
                raise RuntimeError('You must set the environment variable IICS_USERNAME')
        return self._username


def set_up_logging():
    log_format = os.getenv('LOG_FORMAT', '%(levelname)s [%(name)s] %(message)s')
    logging.basicConfig(format=log_format, level=logging.DEBUG, stream=sys.stdout)
    log.debug(f'get-iics-sessions {_version}')
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    if not log_level == 'DEBUG':
        log.debug(f'Changing log level to {log_level}')
    logging.getLogger().setLevel(log_level)


def main():
    set_up_logging()
    client = APIClient()
    for entry in client.get_security_log():
        if entry.get('actionEvent') == 'USER_LOGIN':
            actor = entry.get('actor')
            entry_time = entry.get('entryTime')
            log.info(f'{actor} logged in at {entry_time}')


def handle_sigterm(_signal, _frame):
    sys.exit()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handle_sigterm)
    main()
