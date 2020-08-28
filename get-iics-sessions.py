import apscheduler.schedulers.blocking
import datetime
import fort
import logging
import os
import requests
import signal
import sys

_version = '2020.0'

log = logging.getLogger(__name__)


class Database(fort.PostgresDatabase):
    def add_user_login_timestamp(self, user_id: str, login_timestamp: datetime.datetime):
        sql = '''
            select event_id from environment_usage_events
            where lower(environment_name) = lower(%(environment_name)s)
              and lower(event_name) = lower(%(event_name)s)
              and lower(user_id) = lower(%(user_id)s)
              and event_time = %(event_time)s
        '''
        params = {
            'environment_name': os.getenv('ENVIRONMENT_NAME').lower(),
            'event_name': 'login',
            'user_id': user_id.lower(),
            'event_time': login_timestamp
        }
        existing = self.q_val(sql, params)
        if existing is None:
            self.log.info(f'Adding event to database: {user_id} at {login_timestamp}')
            sql = '''
                insert into environment_usage_events (
                    environment_name, event_name, user_id, event_time
                ) values (
                    lower(%(environment_name)s), lower(%(event_name)s), lower(%(user_id)s), %(event_time)s
                )
            '''
            self.u(sql, params)
        else:
            self.log.info(f'This event is already in the database: {user_id.lower()} at {login_timestamp}')


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


def main_job():
    dsn = os.getenv('DB')
    db = Database(dsn, maxconn=10)
    client = APIClient()
    for entry in client.get_security_log():
        if entry.get('actionEvent') == 'USER_LOGIN':
            actor = entry.get('actor').lower()
            entry_time = datetime.datetime.fromisoformat(entry.get('entryTime')[:-1])
            db.add_user_login_timestamp(actor, entry_time)


def main():
    set_up_logging()
    main_job()
    run_and_exit = os.getenv('RUN_AND_EXIT')
    if run_and_exit is None:
        scheduler = apscheduler.schedulers.blocking.BlockingScheduler()
        sync_interval_hours = int(os.getenv('SYNC_INTERVAL_HOURS', 12))
        scheduler.add_job(main_job, 'interval', hours=sync_interval_hours)
        scheduler.start()


def handle_sigterm(_signal, _frame):
    sys.exit()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, handle_sigterm)
    main()
