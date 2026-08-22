import json
from subprocess import check_output

import pytest
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from syncloudlib.integration.hosts import add_host_alias
from syncloudlib.integration.installer import local_install

TMP_DIR = '/tmp/syncloud'
APP = 'fmd-server'
DATA_DIR = '/var/snap/fmd-server/current'

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


@pytest.fixture(scope="session")
def module_setup(request, device, artifact_dir):
    def module_teardown():
        device.run_ssh('ls -la {0} > {1}/var.current.ls.log'.format(DATA_DIR, TMP_DIR), throw=False)
        device.run_ssh('cat {0}/config/nginx.conf > {1}/nginx.conf.log'.format(DATA_DIR, TMP_DIR), throw=False)
        device.run_ssh('cat {0}/config/fmd-server.yml > {1}/fmd-server.yml.log'.format(DATA_DIR, TMP_DIR), throw=False)
        device.run_ssh('journalctl -u snap.{0}.fmd-server --no-pager | tail -2000 > {1}/fmd-server.log'.format(APP, TMP_DIR), throw=False)
        device.run_ssh('journalctl -u snap.{0}.nginx --no-pager | tail -2000 > {1}/nginx.log'.format(APP, TMP_DIR), throw=False)
        device.run_ssh('journalctl --no-pager | tail -3000 > {0}/journalctl.log'.format(TMP_DIR), throw=False)
        device.scp_from_device('{0}/*'.format(TMP_DIR), artifact_dir)
        check_output('chmod -R a+r {0}'.format(artifact_dir), shell=True)

    request.addfinalizer(module_teardown)


def settle(device):
    device.run_ssh('snap wait system seed.loaded', retries=100, throw=False)
    device.run_ssh('snap set system refresh.hold=2099-01-01T00:00:00Z', retries=20, throw=False)
    device.run_ssh('snap abort --last=auto-refresh', throw=False)
    device.run_ssh('snap watch --last=auto-refresh', throw=False)


def registration_token(device):
    # ssh prints a known-hosts warning into the first command's output
    return device.run_ssh('cat {0}/registration.token'.format(DATA_DIR)).strip().splitlines()[-1].strip()


def register(app_domain, token):
    return requests.put(
        "https://{0}/api/v1/device".format(app_domain),
        json={
            'hashedPassword': 'integration-test-hash',
            'pubKey': 'integration-test-pub',
            'privKey': 'integration-test-priv',
            'salt': 'integration-test-salt',
            'registrationToken': token
        },
        verify=False, timeout=30)


def test_start(module_setup, device, device_host, app, domain):
    add_host_alias(app, device_host, domain)
    device.run_ssh('date', retries=100)
    device.run_ssh('mkdir {0}'.format(TMP_DIR))
    settle(device)


@pytest.mark.flaky(retries=50, delay=10)
def test_activate_device(device):
    device.run_ssh('rm -f /var/snap/platform/current/syncloud.crt', throw=False)
    response = device.activate_custom()
    assert response.status_code == 200, response.text


def test_install(app_archive_path, device_host, device_password):
    local_install(device_host, device_password, app_archive_path)


def wait_for_sockets(device):
    device.run_ssh('test -S {0}/fmd.sock'.format(DATA_DIR), retries=100)
    device.run_ssh('test -S /var/snap/fmd-server/common/web.socket', retries=100)


def test_sockets(device):
    wait_for_sockets(device)


def test_database_in_snap_data(device):
    device.run_ssh('test -f {0}/db/fmd.sqlite'.format(DATA_DIR), retries=100)


@pytest.mark.flaky(retries=10, delay=6)
def test_web(app_domain):
    response = requests.get("https://{0}/".format(app_domain), verify=False,
                            allow_redirects=False, timeout=30)
    assert response.status_code == 200, response.text
    assert 'FMD Server' in response.text, response.text[:200]


@pytest.mark.flaky(retries=10, delay=6)
def test_web_links_to_the_token_page(app_domain):
    response = requests.get("https://{0}/".format(app_domain), verify=False, timeout=30)
    assert 'href="/syncloud"' in response.text, \
        "nginx must inject the token page link into the fmd page: {0}".format(response.text[:400])


def test_token_page_requires_auth(app_domain):
    response = requests.get("https://{0}/syncloud".format(app_domain), verify=False,
                            allow_redirects=False, timeout=30)
    assert response.status_code == 302, \
        "the token page is a secret, it must require a syncloud login: {0}".format(response.status_code)
    assert 'auth.' in response.headers.get('Location', ''), response.headers


@pytest.mark.flaky(retries=10, delay=6)
def test_token_page_shows_the_token(device, app_domain, device_user, device_password):
    session = requests.session()
    response = session.get("https://{0}/syncloud".format(app_domain),
                           auth=(device_user, device_password), verify=False, timeout=30)
    assert response.status_code == 200, response.text
    assert registration_token(device) in response.text, response.text[:400]


@pytest.mark.flaky(retries=10, delay=6)
def test_api_version(app_domain):
    response = requests.get("https://{0}/api/v1/version".format(app_domain), verify=False,
                            allow_redirects=False, timeout=30)
    assert response.status_code == 200, \
        "the FMD app authenticates itself, /api must not be gated: got {0}".format(response.status_code)
    assert response.text.strip() != '', response.text


@pytest.mark.flaky(retries=10, delay=6)
def test_deprecated_root_api(app_domain):
    response = requests.get("https://{0}/version".format(app_domain), verify=False,
                            allow_redirects=False, timeout=30)
    assert response.status_code == 200, \
        "older FMD apps call the v1 endpoints at the root, they must stay open: got {0}".format(
            response.status_code)


def test_registration_requires_token(app_domain):
    response = register(app_domain, 'not-the-token')
    assert response.status_code == 401, \
        "registration must be closed by a token, got {0}: {1}".format(response.status_code, response.text[:200])


@pytest.mark.flaky(retries=10, delay=6)
def test_registration_with_token(device, app_domain):
    response = register(app_domain, registration_token(device))
    assert response.status_code == 200, response.text
    assert json.loads(response.text)['DeviceId'] != '', response.text


def test_no_tcp_ports(device):
    output = device.run_ssh("ss -lntup | grep -c 'fmd-server' || true").strip()
    assert output == '0', "the app must listen on unix sockets only: {0}".format(output)


def test_no_log_files(device):
    output = device.run_ssh("find /var/snap/fmd-server -name '*.log' | wc -l").strip()
    assert output == '0', "logs belong in the journal, not the filesystem: {0}".format(output)


def test_nginx_logs_are_tagged(device):
    output = device.run_ssh('journalctl -t fmd_server_nginx --no-pager | tail -5', retries=10)
    assert 'HTTP/1.1' in output, \
        "nginx access logs must reach the journal under the app's own syslog tag: {0}".format(output)


def test_ctl_lists_registered_user(device):
    output = device.run_ssh('snap run fmd-server.ctl listusers')
    assert 'out of 1' in output, output


def test_remove(device, app):
    response = device.app_remove(app)
    assert response.status_code == 200, response.text


def test_reinstall(app_archive_path, device_host, device_password, device):
    local_install(device_host, device_password, app_archive_path)
    wait_for_sockets(device)


@pytest.mark.flaky(retries=10, delay=6)
def test_api_after_reinstall(app_domain):
    response = requests.get("https://{0}/api/v1/version".format(app_domain), verify=False,
                            allow_redirects=False, timeout=30)
    assert response.status_code == 200, response.text


@pytest.mark.flaky(retries=10, delay=6)
def test_web_after_reinstall(app_domain):
    response = requests.get("https://{0}/".format(app_domain), verify=False,
                            allow_redirects=False, timeout=30)
    assert response.status_code == 200, response.text
    assert 'FMD Server' in response.text, response.text[:200]
