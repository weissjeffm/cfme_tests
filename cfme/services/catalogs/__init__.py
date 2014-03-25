from utils.update import Updateable
import catalog as catalog
import catalog_item as catalog_item
import cfme.web_ui as web_ui
import ui_navigate as nav
import cfme.fixtures.pytest_selenium as sel
import cfme.web_ui.flash as flash


class Catalog(Updateable):
    '''Represents a Catalog'''

    def __init__(self, name=None, description=None, items=None):
        self.name = name
        self.description = description
        self.items = items

    def create(self):
        nav.go_to('catalog_new')
        web_ui.fill(catalog.form, {'name_text': self.name,
                                   'description_text': self.description,
                                   'button_multiselect': self.items},
                    action=catalog.form.add_button)
        flash.assert_no_errors()

    def delete(self):
        nav.go_to('catalog', context={'catalog': self})
        catalog.tb_select("Remove Item from the VMDB", invokes_alert=True)
        sel.handle_alert()
        flash.assert_no_errors()

    def update(self, updates):
        print(updates)
        nav.go_to('catalog_edit', context={'catalog': self})
        web_ui.fill(catalog.form, {'name_text': updates.get('name', None),
                                   'description_text': updates.get('description', None),
                                   'button_multiselect': updates.get('items', None)},
                    action=catalog.form.save_button)


class CatalogItem(Updateable):
    def __init__(self, item_type=None, name=None, description=None, display_in=False, catalog=None, dialog=None):
        self.item_type = item_type
        self.name = name
        self.description = description
        self.display_in = display_in
        self.select_catalog = catalog
        self.select_dialog = dialog

    def create(self):
        nav.go_to('catalog_item_new',context={'provider': self.item_type})
        print  self.item_type+"_____-"
        print  self.select_catalog+"----dialog----"+self.select_dialog
        web_ui.fill(catalog_item.catalog_item_form, {'name_text': self.name,
                                        'description_text': self.description,
                                        'display_checkbox': self.display_in,
                                        'select_catalog': self.select_catalog,
                                        'select_dialog': self.select_dialog},
                    action=catalog.item_form.add_button)
        flash.assert_no_errors()
