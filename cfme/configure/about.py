# -*- coding: utf-8 -*-

from cfme.web_ui import Region

product_assistance = Region(
    locators={
        'quick_start_guide': "//a[.='Quick Start Guide']",
        'installation_guide': "//a[.='Installation Guide']",
        'insight_guide': "//a[.='Insight Guide']",
        'control_guide': "//a[.='Control Guide']",
        'lifecycle_and_automation_guide': "//a[.='Lifecycle and Automation Guide']",
        'integrate_guide': "//a[.='Integrate Guide']",
        'settings_and_operations_guide': "//a[.='Settings and Operations Guide']",
        'red_hat_customer_portal': "//a[.='Red Hat Customer Portal']"
    },
    title='CloudForms Management Engine: About',
    identifying_loc='quick_start_guide'
)
