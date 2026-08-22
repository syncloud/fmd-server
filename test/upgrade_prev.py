from subprocess import check_output

import pytest
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from syncloudlib.integration.hosts import add_host_alias

TMP_DIR = '/tmp/syncloud'
APP = 'fmd-server'

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


@pytest.fixture(scope="session")
def module_setup(request, device, artifact_dir):
    def module_teardown():
        device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)
        device.run_ssh('journalctl --no-pager | tail -3000 > {0}/upgrade-prev.journalctl.log'.format(TMP_DIR),
                       throw=False)
        device.scp_from_device('{0}/*'.format(TMP_DIR), artifact_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def settle(device):
    device.run_ssh('snap wait system seed.loaded', retries=100, throw=False)
    device.run_ssh('snap set system refresh.hold=2099-01-01T00:00:00Z', retries=20, throw=False)
    device.run_ssh('snap abort --last=auto-refresh', throw=False)
    device.run_ssh('snap watch --last=auto-refresh', throw=False)


def test_start(module_setup, device, device_host, app, domain):
    add_host_alias(app, device_host, domain)
    device.run_ssh('date', retries=100)
    device.run_ssh('mkdir -p {0}'.format(TMP_DIR), throw=False)
    settle(device)


@pytest.mark.flaky(retries=50, delay=10)
def test_activate_device(device):
    device.run_ssh('rm -f /var/snap/platform/current/syncloud.crt', throw=False)
    response = device.activate_custom()
    assert response.status_code == 200, response.text


def test_install_released(device, app):
    device.run_ssh('snap remove {0}'.format(app), throw=False)
    device.run_ssh('snap install {0}'.format(app), retries=10)


def test_released_version_serves(device, app_domain):
    device.run_ssh('test -S /var/snap/fmd-server/current/fmd.sock', retries=100)

    response = requests.get("https://{0}/api/v1/version".format(app_domain), verify=False, timeout=30)
    assert response.status_code == 200, response.text
