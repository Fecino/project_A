{
    'name': 'GM POS Access Code',
    'summary': 'Add POS button to generate access codes',
    'version': '1.0.0',
    'author': 'GM',
    'website': 'https://example.com',
    'category': 'Point of Sale',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_access_code_views.xml',
        'views/pos_config_kanban_views.xml',
        'templates/index_custom.xml',
        'templates/access_code_template.xml',
        'reports/access_code_reports.xml',
        'reports/access_code_templates.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos_custom': [
            # Custom POS assets bundle
            'gm_pos_access_code/static/src/css/custom_pos.css',
            'gm_pos_access_code/static/src/js/booking_form.js',
            'gm_pos_access_code/static/src/xml/hide_leftpane.xml',  # Use original working file
            'gm_pos_access_code/static/src/xml/print_dialog.xml',
        ],
        # Remove from original POS assets
        'point_of_sale._assets_pos': [
            # Keep original POS clean - no custom modifications
        ],
    },
    'installable': True,
}
