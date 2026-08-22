from subprocess import check_output

import pytest
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.installer import local_install

TMP_DIR = '/tmp/syncloud'
DATA_DIR = '/var/snap/fmd-server/current'

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


@pytest.fixture(scope="session")
def module_setup(request, device, artifact_dir):
    def module_teardown():
        device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl --no-pager | tail -3000 > {0}/upgrade.journalctl.log'.format(TMP_DIR), throw=False)
        device.scp_from_device('{0}/*'.format(TMP_DIR), artifact_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def token(device):
    return device.run_ssh('cat {0}/registration.token'.format(DATA_DIR)).strip()


@pytest.fixture(scope="session")
def before(device):
    return {'token': token(device), 'users': device.run_ssh('snap run fmd-server.ctl listusers')}


def test_start(module_setup, before, device_host, app, domain):
    add_host_alias(app, device_host, domain)


def test_upgrade(device_host, device_password, app_archive_path, device):
    local_install(device_host, device_password, app_archive_path)
    device.run_ssh('test -S {0}/fmd.sock'.format(DATA_DIR), retries=100)
    device.run_ssh('test -S /var/snap/fmd-server/common/web.socket', retries=100)


@pytest.mark.flaky(retries=10, delay=6)
def test_web_after_upgrade(app_domain):
    response = requests.get("https://{0}/".format(app_domain), verify=False,
                            allow_redirects=False, timeout=30)
    assert response.status_code == 200, response.text
    assert 'FMD Server' in response.text, response.text[:200]


def test_registration_token_survived(device, before):
    assert token(device) == before['token'], \
        "a new token would unpair every phone that has the old one"


def test_account_survived(device, before):
    assert 'out of 1' in device.run_ssh('snap run fmd-server.ctl listusers'), \
        "the account registered before the refresh must still exist"
