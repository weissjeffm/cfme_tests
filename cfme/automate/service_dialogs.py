import cfme.fixtures.pytest_selenium as sel
from selenium.webdriver.common.by import By
import cfme.web_ui.accordion as accordion
from utils.update import Updateable
from cfme.web_ui import Form, fill
import cfme.web_ui.toolbar as tb
import ui_navigate as nav
import functools


tb_select = functools.partial(tb.select, "Configuration")

label_form = Form(
    fields=
    [('label', (By.CSS_SELECTOR, "input#label")),
     ('description_text', (By.CSS_SELECTOR, "input#description")),
     ('submit_button', (By.CSS_SELECTOR, "input#chkbx_submit")),
     ('cancel_button', (By.CSS_SELECTOR, "input#chkbx_cancel")),
     ('plus_button', (By.CSS_SELECTOR, "div.dhx_toolbar_btn over[title='Add']")),
     ('add_tab_button', (By.CSS_SELECTOR, "tr.tr_btn[title='Add a New Tab to this Dialog']"))])

tab_form = Form(
    fields=
    [('label', (By.CSS_SELECTOR, "input#tab_label")),
     ('description_text', (By.CSS_SELECTOR, "input#tab_description")),
     ('plus_button', (By.CSS_SELECTOR, "div.dhx_toolbar_arw[title='Add']")),
     ('add_box_button', (By.CSS_SELECTOR, "tr.tr_btn[title='Add a New Box to this Tab']"))])

box_form = Form(
    fields=
    [('label', (By.CSS_SELECTOR, "input#group_label")),
     ('description_text', (By.CSS_SELECTOR, "input#group_description")),
     ('plus_button', (By.CSS_SELECTOR, "div.dhx_toolbar_arw[title='Add']")),
     ('add_element_button', (By.CSS_SELECTOR, "tr.tr_btn[title='Add a New Element to this Box']"))])

element_form = Form(
    fields=
    [('label', (By.CSS_SELECTOR, "input#field_label")),
     ('description_text', (By.CSS_SELECTOR, "input#description")),
     ('add_button', "img[title='Add']")])


def dialog_in_tree(catalog_item):
    return ("//div[@id='sandt_tree_div']//td[@class='standartTreeRow']/span[.='%s']"
        % catalog_item.name)


def _all_servicedialogs_add_new(context):
    sel.click("//div[@id='dialogs_tree_div']//td[.='All Dialogs']")
    tb_select('Add a new Dialog')
    sel.wait_for_element(label_form.label)

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
        nav.go_to('service_dialog_new')
        fill(label_form, {'label': self.label,
                          'description_text': self.description,
                          'submit_button': self.submit,
                          'cancel_button': self.cancel},
            action=label_form.plus_button)
        sel.click(label_form.add_tab_button)
