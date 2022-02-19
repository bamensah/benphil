# -*- coding: utf-8 -*-
{
    'name': "peg_finance_mods",

    'summary': """
        Collective for modifications to the PEG finance module""",

    'description': """
        Additional features to the finance core module:
        Department Mapping
    """,

    'author': "sfiam-coblavie@pegafrica.com",
    'website': "https://www.pegafrica.com",

    'category': 'Accounting',
    'version': '0.2',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'account',
        'analytic',
        'studio_customization',#Addded MIG14
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
#        'views/templates.xml',
        'views/analytic_views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto-install': True
}
