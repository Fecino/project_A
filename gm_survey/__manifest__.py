# -*- coding: utf-8 -*-
{
    'name': "Scentzania Custom Survey",

    'summary': "Custom, mobile-friendly survey flow for Scentzania with beautiful UI/UX.",

    'description': """
Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'survey', 'survey_crm_generation', 'gm_web', 'gm_scentopia', 'queue_job'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data_20_question.xml',
        'data/paperformat.xml',
        # 'data/data_40_question.xml',
        'views/views.xml',
        'static/src/xml/survey_page.xml',
        'static/src/xml/custom_template.xml',
        'static/src/xml/survey_print.xml',
        'static/src/xml/avatar_view.xml',
        'static/src/xml/avatar_profile.xml',
        'static/src/xml/choose_report.xml',
        'static/src/xml/ayurvedic_dosha_report.xml',
        'static/src/xml/career_match_report.xml',
        'static/src/xml/five_elements_report.xml',
        'static/src/xml/love_match_report.xml',
        'static/src/xml/soulfulness_report.xml',
        'static/src/xml/tcm_report.xml',
        'static/src/xml/thirty_one_types_report.xml',
        'static/src/xml/send_email_report.xml',
        'report/avatar_detail_report.xml',
        'report/avatar_page_1.xml',
        'report/avatar_page_5.xml',
        'report/avatar_page_6.xml',
        'report/avatar_page_9.xml',
        'report/avatar_intensity_index.xml',
        'report/avatar_intensity_table.xml',
        
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'assets': {
        'survey.survey_assets': [
            'gm_survey/static/src/js/survey.js',
        ],
        'web.report_assets_common': [
            'gm_survey/static/src/scss/font.scss',
        ],
        'web.assets_frontend': [
            'gm_survey/static/src/scss/font.scss',
        ],
    }
}

