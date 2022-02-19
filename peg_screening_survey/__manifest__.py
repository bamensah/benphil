# -*- coding: utf-8 -*-
{
    'name': "Survey Screening Call",

    'summary': """
        Expansion for the survey module for customizations for Screening Calls (PEG)""",

    'description': """
        Long description of module's purpose
    """,

    'author': "PEG Africa",
    'website': "http://www.pegafrica.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'module_category_survey',
    'version': '1.1',

    # any module necessary for this one to work correctly

    'depends': ['base', 'survey', 'partner_survey'],


    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'application': True,
}
