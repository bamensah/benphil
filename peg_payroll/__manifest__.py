# -*- coding: utf-8 -*-
{
    'name': "PEG Payroll Extension",

    'summary': """
        Modifications to the Payroll feature""",

    'description': """
        Modifications to the Payroll feature specific to PEG Africa
    """,

    'author': "PEG Africa",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_payroll'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_employee.xml'
    ]
}
