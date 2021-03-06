""" A model of an Infrastructure Host in CFME


:var page: A :py:class:`cfme.web_ui.Region` object describing common elements on the
           Providers pages.
:var properties_form: A :py:class:`cfme.web_ui.Form` object describing the main add form.
:var credentials_form: A :py:class:`cfme.web_ui.Form` object describing the credentials form.
"""

from functools import partial

import ui_navigate as nav

import cfme
import cfme.fixtures.pytest_selenium as sel
import cfme.web_ui.flash as flash
import cfme.web_ui.menu  # so that menu is already loaded before grafting onto it
import cfme.web_ui.toolbar as tb
import utils.conf as conf
from cfme.web_ui import Region, Quadicon, Form, Select, Tree, fill, paginator
from utils.ipmi import IPMI
from utils.log import logger
from utils.update import Updateable
from utils.wait import wait_for


# Common locators
page_specific_locators = Region(
    locators={
        'cancel_button': "//img[@title='Cancel']",
        'creds_validate_btn': "//div[@id='default_validate_buttons_on']"
                              "/ul[@id='form_buttons']/li/a/img",
        'creds_verify_disabled_btn': "//div[@id='default_validate_buttons_off']"
                                     "/ul[@id='form_buttons']/li/a/img",
    }
)

# Page specific locators
add_page = Region(
    locators={
        'add_submit': "//img[@alt='Add this Host']",
    },
    title='CloudForms Management Engine: Hosts')

edit_page = Region(
    locators={
        'save_button': "//img[@title='Save Changes']",
    })

manage_policies_page = Region(
    locators={
        'save_button': "//div[@id='buttons_on']//img[@alt='Save Changes']",
    })

details_page = Region(infoblock_type='detail')

properties_form = Form(
    fields=[
        ('name_text', "//*[@id='name']"),
        ('hostname_text', "//*[@id='hostname']"),
        ('ipaddress_text', "//*[@id='ipaddress']"),
        ('custom_ident_text', "//*[@id='custom_1']"),
        ('host_platform', Select('//select[@id="user_assigned_os"]')),
        ('ipmi_address_text', "//*[@id='ipmi_address']"),
        ('mac_address_text', "//*[@id='mac_address']"),
    ])

credential_form = Form(
    fields=[
        ('default_button', "//div[@id='auth_tabs']/ul/li/a[@href='#default']"),
        ('default_principal', "//*[@id='default_userid']"),
        ('default_secret', "//*[@id='default_password']"),
        ('default_verify_secret', "//*[@id='default_verify']"),
        ('ipmi_button', "//div[@id='auth_tabs']/ul/li/a[@href='#ipmi']"),
        ('ipmi_principal', "//*[@id='ipmi_userid']"),
        ('ipmi_secret', "//*[@id='ipmi_password']"),
        ('ipmi_verify_secret', "//*[@id='ipmi_verify']"),
        ('validate_btn', page_specific_locators.creds_validate_btn)
    ])

manage_policies_form = Form(
    fields=[
        ('policy_select', Tree("//div[@id='treebox']/div/table")),
    ])

cfg_btn = partial(tb.select, 'Configuration')
pol_btn = partial(tb.select, 'Policy')
pow_btn = partial(tb.select, 'Power')

nav.add_branch('infrastructure_hosts',
               {'infrastructure_host_new': lambda _: cfg_btn(
                   'Add a New Host'),
                'infrastructure_host_discover': lambda _: cfg_btn(
                    'Discover Hosts'),
                'infrastructure_host': [lambda ctx: sel.click(Quadicon(ctx['host'].name,
                                                                      'host')),
                                   {'infrastructure_host_edit':
                                    lambda _: cfg_btn('Edit this Host'),
                                    'infrastructure_host_policy_assignment':
                                    lambda _: pol_btn('Manage Policies')}]})


class Host(Updateable):
    """
    Model of an infrastructure host in cfme.

    Args:
        name: Name of the host.
        hostname: Hostname of the host.
        ip_address: The IP address as a string.
        custom_ident: The custom identifiter.
        host_platform: Included but appears unused in CFME at the moment.
        ipmi_address: The IPMI address.
        mac_address: The mac address of the system.
        credentials (Credential): see Credential inner class.
        ipmi_credentials (Credential): see Credential inner class.

    Usage:

        myhost = Host(name='vmware',
                      credentials=Provider.Credential(principal='admin', secret='foobar'))
        myhost.create()

    """

    def __init__(self, name=None, hostname=None, ip_address=None, custom_ident=None,
                 host_platform=None, ipmi_address=None, mac_address=None, credentials=None,
                 ipmi_credentials=None, interface_type='lan'):
        self.name = name
        self.hostname = hostname
        self.ip_address = ip_address
        self.custom_ident = custom_ident
        self.host_platform = host_platform
        self.ipmi_address = ipmi_address
        self.mac_address = mac_address
        self.credentials = credentials
        self.ipmi_credentials = ipmi_credentials
        self.interface_type = interface_type

    def _form_mapping(self, create=None, **kwargs):
        return {'name_text': kwargs.get('name'),
                'hostname_text': kwargs.get('hostname'),
                'ipaddress_text': kwargs.get('ip_address'),
                'custom_ident_text': kwargs.get('custom_ident'),
                'host_platform': kwargs.get('host_platform'),
                'ipmi_address_text': kwargs.get('ipmi_address'),
                'mac_address_text': kwargs.get('mac_address')}

    class Credential(cfme.Credential, Updateable):
        """Provider credentials

           Args:
             **kwargs: If using IPMI type credential, ipmi = True"""

        def __init__(self, **kwargs):
            super(Host.Credential, self).__init__(**kwargs)
            self.ipmi = kwargs.get('ipmi')

    def _submit(self, cancel, submit_button):
        if cancel:
            sel.click(page_specific_locators.cancel_button)
            # sel.wait_for_element(page.configuration_btn)
        else:
            sel.click(submit_button)
            flash.assert_no_errors()

    def create(self, cancel=False, validate_credentials=False):
        """
        Creates a host in the UI

        Args:
           cancel (boolean): Whether to cancel out of the creation.  The cancel is done
               after all the information present in the Host has been filled in the UI.
           validate_credentials (boolean): Whether to validate credentials - if True and the
               credentials are invalid, an error will be raised.
        """
        sel.force_navigate('infrastructure_host_new')
        fill(properties_form, self._form_mapping(True, **self.__dict__))
        fill(credential_form, self.credentials, validate=validate_credentials)
        fill(credential_form, self.ipmi_credentials, validate=validate_credentials)
        self._submit(cancel, add_page.add_submit)

    def update(self, updates, cancel=False, validate_credentials=False):
        """
        Updates a host in the UI.  Better to use utils.update.update context
        manager than call this directly.

        Args:
           updates (dict): fields that are changing.
           cancel (boolean): whether to cancel out of the update.
        """

        sel.force_navigate('infrastructure_host_edit', context={'host': self})
        fill(properties_form, self._form_mapping(**updates))
        fill(credential_form, updates.get('credentials', None), validate=validate_credentials)
        self._submit(cancel, edit_page.save_button)

    def delete(self, cancel=True):
        """
        Deletes a host from CFME

        Args:
            cancel: Whether to cancel the deletion, defaults to True
        """

        sel.force_navigate('infrastructure_host', context={'host': self})
        cfg_btn('Remove from the VMDB', invokes_alert=True)
        sel.handle_alert(cancel=cancel)

    def power_on(self):
        sel.force_navigate('infrastructure_host', context={'host': self})
        pow_btn('Power On')
        sel.handle_alert()

    def power_off(self):
        sel.force_navigate('infrastructure_host', context={'host': self})
        pow_btn('Power Off')
        sel.handle_alert()

    def get_ipmi(self):
        return IPMI(hostname=self.ipmi_address, username=self.ipmi_credentials.principal,
                    password=self.ipmi_credentials.secret, interface_type=self.interface_type)

    def get_detail(self, *ident):
        """ Gets details from the details infoblock

        The function first ensures that we are on the detail page for the specific host.

        Args:
            *ident: An InfoBlock title, followed by the Key name, e.g. "Relationships", "Images"
        Returns: A string representing the contents of the InfoBlock's value.
        """
        if not self._on_detail_page():
            sel.force_navigate('infrastructure_host', context={'host': self})
        return details_page.infoblock.text(*ident)

    def _on_detail_page(self):
        """ Returns ``True`` if on the hosts detail page, ``False`` if not."""
        return sel.is_displayed('//div[@class="dhtmlxInfoBarLabel-2"][contains(., "%s")]'
                                % self.name)

    @property
    def exists(self):
        sel.force_navigate('infrastructure_hosts')
        for page in paginator.pages():
            if sel.is_displayed(Quadicon(self.name, 'host')):
                return True
        else:
            return False

    @property
    def _all_available_policy_profiles(self):
        pp_rows_locator = "//table/tbody/tr/td[@class='standartTreeImage']"\
            "/img[contains(@src, 'policy_profile')]/../../td[@class='standartTreeRow']"
        return sel.elements(pp_rows_locator)

    def _is_policy_profile_row_checked(self, row):
        return "Check" in row.find_element_by_xpath("../td[@width='16px']/img").get_attribute("src")

    @property
    def _assigned_policy_profiles(self):
        result = set([])
        for row in self._all_available_policy_profiles:
            if self._is_policy_profile_row_checked(row):
                result.add(row.text.encode("utf-8"))
        return result

    def get_assigned_policy_profiles(self):
        """ Return a set of Policy Profiles which are available and assigned.

        Returns: :py:class:`set` of :py:class:`str` of Policy Profile names
        """
        sel.force_navigate('infrastructure_host_policy_assignment', context={'host': self})
        return self._assigned_policy_profiles

    @property
    def _unassigned_policy_profiles(self):
        result = set([])
        for row in self._all_available_policy_profiles:
            if not self._is_policy_profile_row_checked(row):
                result.add(row.text.encode("utf-8"))
        return result

    def get_unassigned_policy_profiles(self):
        """ Return a set of Policy Profiles which are available but not assigned.

        Returns: :py:class:`set` of :py:class:`str` of Policy Profile names
        """
        sel.force_navigate('infrastructure_host_policy_assignment', context={'host': self})
        return self._unassigned_policy_profiles

    def _assign_unassign_policy_profiles(self, assign, *policy_profile_names):
        """ Assign or unassign Policy Profiles to this Provider. DRY method

        Args:
            assign: Whether this method assigns or unassigns policy profiles.
            policy_profile_names: :py:class:`str` with Policy Profile's name. After Control/Explorer
                coverage goes in, PolicyProfile object will be also passable.
        """
        sel.force_navigate('infrastructure_host_policy_assignment', context={'host': self})
        policy_profiles = set([str(pp) for pp in policy_profile_names])
        if assign:
            do_not_process = self._assigned_policy_profiles
        else:
            do_not_process = self._unassigned_policy_profiles
        fill(
            manage_policies_form,
            dict(policy_select=[(x,) for x in list(policy_profiles - do_not_process)]),
            action=manage_policies_page.save_button
        )

    def assign_policy_profiles(self, *policy_profile_names):
        """ Assign Policy Profiles to this Host.

        Args:
            policy_profile_names: :py:class:`str` with Policy Profile names. After Control/Explorer
                coverage goes in, PolicyProfile objects will be also passable.
        """
        self._assign_unassign_policy_profiles(True, *policy_profile_names)

    def unassign_policy_profiles(self, *policy_profile_names):
        """ Unssign Policy Profiles to this Host.

        Args:
            policy_profile_names: :py:class:`str` with Policy Profile names. After Control/Explorer
                coverage goes in, PolicyProfile objects will be also passable.
        """
        self._assign_unassign_policy_profiles(False, *policy_profile_names)


@fill.method((Form, Host.Credential))
def _fill_credential(form, cred, validate=None):
    """How to fill in a credential (either ipmi or default).  Validates the
    credential if that option is passed in.
    """
    if cred.ipmi:
        fill(credential_form, {'ipmi_button': True,
                               'ipmi_principal': cred.principal,
                               'ipmi_secret': cred.secret,
                               'ipmi_verify_secret': cred.verify_secret,
                               'validate_btn': validate})
    else:
        fill(credential_form, {'default_principal': cred.principal,
                               'default_secret': cred.secret,
                               'default_verify_secret': cred.verify_secret,
                               'validate_btn': validate})
    if validate:
        flash.assert_no_errors()


def get_credentials_from_config(credential_config_name):
    creds = conf.credentials[credential_config_name]
    return Host.Credential(principal=creds['username'],
                           secret=creds['password'])


def get_from_config(provider_config_name):
    """
    Creates a Host object given a yaml entry in cfme_data.

    Usage:
        get_from_config('esx')

    Returns: A Host object that has methods that operate on CFME
    """

    prov_config = conf.cfme_data['management_hosts'][provider_config_name]
    credentials = get_credentials_from_config(prov_config['credentials'])
    ipmi_credentials = get_credentials_from_config(prov_config['ipmi_credentials'])
    ipmi_credentials.ipmi = True

    return Host(name=prov_config['name'],
                hostname=prov_config['hostname'],
                ip_address=prov_config['ipaddress'],
                custom_ident=prov_config['custom_ident'],
                host_platform=prov_config['host_platform'],
                ipmi_address=prov_config['ipmi_address'],
                mac_address=prov_config['mac_address'],
                interface_type=prov_config['interface_type'],
                credentials=credentials,
                ipmi_credentials=ipmi_credentials)


def wait_for_a_host():
    sel.force_navigate('infrastructure_hosts')
    logger.info('Waiting for a host to appear...')
    wait_for(paginator.rec_total, fail_condition=None, message="Wait for any host to appear",
             num_sec=1000, fail_func=sel.refresh)


def wait_for_host_delete(host):
    sel.force_navigate('infrastructure_hosts')
    quad = Quadicon(host.name, 'host')
    logger.info('Waiting for a host to delete...')
    wait_for(lambda prov: not sel.is_displayed(prov), func_args=[quad], fail_condition=False,
             message="Wait host to disappear", num_sec=1000, fail_func=sel.refresh)
