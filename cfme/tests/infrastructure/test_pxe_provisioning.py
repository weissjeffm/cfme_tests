import pytest

from utils.conf import cfme_data
from cfme.infrastructure.provisioning import provisioning_form
from cfme.infrastructure.pxe import get_pxe_server_from_config, get_template_from_config
from cfme.services import requests
from cfme.web_ui import flash, fill
from utils import testgen
from utils.providers import setup_infrastructure_providers
from utils.randomness import generate_random_string
from utils.log import logger
from utils.wait import wait_for

pytestmark = [
    pytest.mark.fixtureconf(server_roles="+automate"),
    pytest.mark.usefixtures('server_roles', 'uses_infra_providers')
]


def pytest_generate_tests(metafunc):
    # Filter out providers without provisioning data or hosts defined
    argnames, argvalues, idlist = testgen.infra_providers(metafunc, 'provisioning')
    pargnames, pargvalues, pidlist = testgen.pxe_servers(metafunc)
    argnames = argnames + ['pxe_server', 'pxe_cust_template']
    pxe_server_names = [pval[0] for pval in pargvalues]

    new_idlist = []
    new_argvalues = []
    for i, argvalue_tuple in enumerate(argvalues):
        args = dict(zip(argnames, argvalue_tuple))
        if not args['provisioning']:
            # No provisioning data available
            continue

        # required keys should be a subset of the dict keys set
        if not {'pxe_template', 'host', 'datastore',
                'pxe_server', 'pxe_image', 'pxe_kickstart',
                'pxe_root_password',
                'pxe_image_type', 'vlan'}.issubset(args['provisioning'].viewkeys()):
            # Need all  for template provisioning
            continue

        pxe_server_name = args['provisioning']['pxe_server']
        if pxe_server_name not in pxe_server_names:
            continue

        pxe_cust_template = args['provisioning']['pxe_kickstart']
        if pxe_cust_template not in cfme_data['customization_templates'].keys():
            continue

        argvalues[i].append(get_pxe_server_from_config(pxe_server_name))
        argvalues[i].append(get_template_from_config(pxe_cust_template))
        new_idlist.append(idlist[i])
        new_argvalues.append(argvalues[i])

    testgen.parametrize(metafunc, argnames, new_argvalues, ids=new_idlist, scope="module")


@pytest.fixture(scope="module")
def setup_providers():
    # Normally function-scoped
    setup_infrastructure_providers()


@pytest.fixture(scope="module")
def setup_pxe_servers_vm_prov(pxe_server, pxe_cust_template, provisioning):
    if not pxe_server.exists():
        pxe_server.create()
    pxe_server.set_pxe_image_type(provisioning['pxe_image'], provisioning['pxe_image_type'])
    if not pxe_cust_template.exists():
        pxe_cust_template.create()


@pytest.yield_fixture(scope="function")
def vm_name(provider_key, provider_mgmt):
    # also tries to delete the VM that gets made with this name
    vm_name = 'provtest-%s' % generate_random_string()
    yield vm_name
    try:
        logger.info('Cleaning up VM %s on provider %s' % (vm_name, provider_key))
        provider_mgmt.delete_vm(vm_name)
    except:
        # The mgmt_sys classes raise Exception :\
        logger.warning('Failed to clean up VM %s on provider %s' % (vm_name, provider_key))


@pytest.mark.usefixtures('setup_pxe_servers_vm_prov')
def test_pxe_provision_from_template(setup_providers, provider_crud, provider_type,
                                     provider_mgmt, provisioning, vm_name):

    # generate_tests makes sure these have values
    pxe_template, host, datastore, pxe_server, pxe_image, pxe_kickstart,\
        pxe_root_password, pxe_image_type, pxe_vlan = map(provisioning.get, ('pxe_template', 'host',
                                'datastore', 'pxe_server', 'pxe_image', 'pxe_kickstart',
                                'pxe_root_password', 'pxe_image_type', 'vlan'))
    pytest.sel.force_navigate('infrastructure_provision_vms', context={
        'provider': provider_crud,
        'template_name': pxe_template,
    })

    note = ('template %s to vm %s on provider %s' %
        (pxe_template, vm_name, provider_crud.key))
    provisioning_data = {
        'email': 'template_provisioner@example.com',
        'first_name': 'Template',
        'last_name': 'Provisioner',
        'notes': note,
        'vm_name': vm_name,
        'host_name': {'name': [host]},
        'datastore_name': {'name': [datastore]},
        'provision_type': 'PXE',
        'pxe_server': pxe_server,
        'pxe_image': {'name': [pxe_image]},
        'custom_template': {'name': [pxe_kickstart]},
        'root_password': pxe_root_password,
        'vlan': pxe_vlan,
    }

    fill(provisioning_form, provisioning_data, action=provisioning_form.submit_button)
    flash.assert_no_errors()

    # Wait for the VM to appear on the provider backend before proceeding to ensure proper cleanup
    logger.info('Waiting for vm %s to appear on provider %s', vm_name, provider_crud.key)
    wait_for(provider_mgmt.does_vm_exist, [vm_name], handle_exception=True, num_sec=600)

    # nav to requests page happens on successful provision
    logger.info('Waiting for cfme provision request for vm %s' % vm_name)
    row_description = 'Provision from [%s] to [%s]' % (pxe_template, vm_name)
    cells = {'Description': row_description}

    row, __ = wait_for(requests.wait_for_request, [cells],
        fail_func=requests.reload, num_sec=1500, delay=20)
    assert row.last_message.text == 'VM Provisioned Successfully'
