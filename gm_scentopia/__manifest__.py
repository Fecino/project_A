# -*- coding: utf-8 -*-
{
    'name': "gm_scentopia",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '18.0.1.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'survey', 'crm','sale','sale_management','hr','delivery'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/perfume.details.csv',
        'data/data_ir_cron.xml',
        'data/data_fragrance_family.xml',
        'data/data_intensity.xml',
        'data/data_avatar.xml',
        'views/menuitem.xml',
        'views/crm_form_inherit.xml',
        'views/fragrance_families.xml',
        'views/scentopia_avatar.xml',
        'views/product_template.xml',
        'views/res_partner.xml',
        'views/sale_order.xml',
        'views/info_card.xml',
        'views/trivia_card.xml',
        'views/res_users.xml',
        'views/res_config_settings.xml',

        'views/perfume_details.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
