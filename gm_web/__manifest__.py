# -*- coding: utf-8 -*-
{
    'name': "Scentopia Web Module",

    'summary': "Frontend web interface for Scentopia perfume creation and bottling experience",

    'description': """
Scentopia Web Frontend Module
==============================

This module provides a comprehensive web interface for the Scentopia perfume creation platform.

Key Features:
-------------
* Custom authentication and user signup flows
* Interactive perfume formula browsing and selection
* Guided perfume creation journey with step-by-step instructions
* Real-time bottling process visualization (drop, pump, seal stages)
* Formula naming and customization
* Staff validation and access control
* Responsive frontend templates and assets
* Enhanced user profile management with partner firstname support

The module includes:
* Complete authentication templates (login, signup, user management)
* Perfume journey workflow (intro, oil dropping, formula creation)
* Formula management (browsing, details, purchased formulas)
* Bottling workflow (start, pump, seal, finish)
* Custom CSS styling and JavaScript validation
* Error handling and 404 pages
    """,

    'author': "Gleematic Ltd",
    'website': "https://gleematic.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'auth_signup','partner_firstname', 'gm_scentopia'],

    # always loaded
    'data': [
        'data/scentopia_web_data.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/scentopia_web.xml',
        'views/res_partner_view.xml',
        # Core templates
        'static/src/xml/website.xml',
        'static/src/xml/404_error.xml',
        
        # Authentication
        'static/src/xml/auth_login.xml',
        'static/src/xml/auth_signup.xml',
        'static/src/xml/auth_user.xml',
        'static/src/xml/auth_choose_test.xml',
        
        # Perfume Journey (in order of flow)
        'static/src/xml/home_page.xml',
        'static/src/xml/formula_all_page.xml',
        'static/src/xml/formula_detail_page.xml',
        'static/src/xml/formula_purchased_all_page.xml',
        'static/src/xml/formula_purchased_detail_page.xml',
        'static/src/xml/formula_bottling_start_page.xml',
        'static/src/xml/formula_bottling_pump_page.xml',
        'static/src/xml/formula_bottling_seal_page.xml',
        'static/src/xml/formula_bottling_finish_page.xml',
        'static/src/xml/perfume_journey_create_page.xml',
        'static/src/xml/access_page.xml',
        'static/src/xml/pre_intro_page.xml',
        'static/src/xml/intro_page.xml',
        'static/src/xml/post_intro_page.xml',

        'static/src/xml/perfume_start_01_drop.xml',
        'static/src/xml/perfume_start_02_drop.xml',
        'static/src/xml/perfume_start_drop_oil.xml',
        'static/src/xml/perfume_start_drop_oil_added.xml',
        'static/src/xml/perfume_start_drop_oil_maxed.xml',
        'static/src/xml/perfume_journey_formula_naming_page.xml',

        'static/src/xml/invalid_perfume.xml',
        'static/src/xml/change_value.xml',
        'static/src/xml/staff_validation.xml',
        'static/src/xml/bottling_access_page.xml',

        'static/src/xml/05_perfume_category_drop.xml',
        'static/src/xml/05_perfume_category_drop_edit.xml',

        'static/src/xml/thank_you.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    'assets': {
        'web.assets_frontend': [
            'gm_web/static/src/css/modal.css',
            'gm_web/static/src/css/user.css',
            'gm_web/static/src/css/auth_override.css',
            # 'gm_web/static/src/css/portal_my_home.css',
            # 'gm_web/static/src/css/perfume_test.css',
            'gm_web/static/src/js/select_country.js',
            'gm_web/static/src/js/validate.js',
            'gm_web/static/src/js/user.js',
        ],
    },
}
