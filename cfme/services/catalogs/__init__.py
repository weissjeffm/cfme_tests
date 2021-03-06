from utils.update import Updateable
import catalog as catalog
import cfme.web_ui as web_ui
import cfme.fixtures.pytest_selenium as sel
import cfme.web_ui.flash as flash


class Catalog(Updateable):
    """Represents a Catalog"""

    def __init__(self, name=None, description=None, items=None):
        self.name = name
        self.description = description
        self.items = items

    def create(self):
        sel.force_navigate('catalog_new')
        web_ui.fill(catalog.form, {'name_text': self.name,
                                   'description_text': self.description,
                                   'button_multiselect': self.items},
                    action=catalog.form.add_button)
        flash.assert_no_errors()

    def delete(self):
        sel.force_navigate('catalog', context={'catalog': self})
        catalog.tb_select("Remove Item from the VMDB", invokes_alert=True)
        sel.handle_alert()
        flash.assert_no_errors()

    def update(self, updates):
        print(updates)
        sel.force_navigate('catalog_edit', context={'catalog': self})
        web_ui.fill(catalog.form, {'name_text': updates.get('name', None),
                                   'description_text': updates.get('description', None),
                                   'button_multiselect': updates.get('items', None)},
                    action=catalog.form.save_button)
