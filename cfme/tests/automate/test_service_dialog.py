import cfme.web_ui.flash as flash
from cfme.automate.service_dialogs import ServiceDialog
import utils.randomness as rand


def test_create_service_dialog():
    dialog = ServiceDialog(label=rand.generate_random_string(),
                  description="my dialog", submit=True, cancel=True)
    dialog.create()
    flash.assert_no_errors()
