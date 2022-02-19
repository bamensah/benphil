# -*- coding: utf-8 -*-
{
    'name': "studio peg extended views",

    'summary': """
       Studio PEG Extended Views""",

    'description': """
        Studio PEG Extended Views
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    'category': 'Management',
    'version': '14.1.0.0',

    'depends': [
        'base',
        'account',
        'hr_payroll',
        'survey',
        'stock_landed_costs',
        'stock',
        'stock_picking_cancel_extention',
        'stock_no_negative',
        'studio_customization',
        'peg_dev_module',
    ],

    'data': [
        'views/account_move_form.xml',
        'views/account_journal_views.xml',
        'views/view_move_tree.xml',
        'views/view_account_payment_form.xml',
        'views/view_account_analytic_account_list.xml',
        'views/view_account_analytic_account_form.xml',
        'views/view_account_analytic_line_form.xml',
        'views/view_partner_form.xml',
        'views/view_partner_tree.xml',
        'views/view_employee_form.xml',
        'views/hr_salary_rule_list.xml',
        'views/survey_user_input_view_form.xml',
        'views/view_stock_landed_cost_form.xml',
        'views/product_category_form_view.xml',
        'views/stock_valuation_layer_tree.xml',
        'views/product_template_only_form_view.xml',
        'views/purchase_order_form.xml',
        'views/purchase_order_tree.xml',
        'views/view_order_form.xml',
        'views/sale_views.xml',
        'views/stock_production_lot_view.xml',
        'views/view_stock_move_tree.xml',
        'views/stock_move_line_view.xml',
        'views/stock_location_views.xml',
        'views/stock_picking_type_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': True,
}
