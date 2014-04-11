import ui_navigate as nav
import cfme.fixtures.pytest_selenium as sel
from cfme.web_ui import Form, fill
from utils.update import Updateable
import cfme.web_ui.accordion as accordion
import cfme.web_ui.toolbar as tb
import functools
import time

tb_select = functools.partial(tb.select, "Configuration")

label_form = Form(
    fields=
    [('label', "input[name='label']"),
     ('description_text', "input[name='description']"),
     ('submit_button', "input[name='chkbx_submit']"),
     ('cancel_button', "input[name='chkbx_cancel']"),
     ('add_button', "img[title='Add']")])


def dialog_in_tree(catalog_item):
    return ("//div[@id='sandt_tree_div']//td[@class='standartTreeRow']/span[.='%s']"
        % catalog_item.name)


def _all_servicedialogs_add_new(context):
    sel.click("//div[@id='dialogs_tree_div']//td[.='All Dialogs']")
    tb_select('Add a New Dialog')

nav.add_branch(
    'automate_customization',
    {'service_dialogs': [nav.partial(accordion.click, 'Service Dialogs'),
                       {'service_dialog_new': _all_servicedialogs_add_new}]})


class ServiceDialog(Updateable):

    def __init__(self, label=None, description=None,
        submit=False, cancel=False):
        self.label = label
        self.description = description
        self.submit = submit
        self.cancel = cancel

    def create(self):
        sel.force_navigate('service_dialog_new')
        time.sleep(5)
        fill(label_form, {'label': self.label,
                          'description_text': self.description,
                          'submit_button': self.submit,
                          'cancel_button': self.cancel})
        print "baba black sheep"
        sel.click(label_form.add_button)
