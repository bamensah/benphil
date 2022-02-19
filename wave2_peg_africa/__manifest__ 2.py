# -*- coding: utf-8 -*-
{
    'name': "wave2_peg_africa",

    'summary': """Wave 2 module to manage Sale, CRM, Accounting, Inventory, Helpdesk, API Gateway for PEG-AFRICA""",

    'description': """
        Adaptation of Odoo modules
    """,

    'author': "Niang Serigne Ahmadou, Mame Daba Diouf",
    'website': "https://www.it4life.org",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Test',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'account','sale_management', 'sales_custom_quotation_template', 'peg_dev_module',
                'sale','purchase','sale_stock', 'sale_crm','crm', 'repair', 'account_reports', 'purchase_tripple_approval',
                'base_geolocalize', 'stock'],
    # account_cancel
    # always loaded
    'data': [
        'data/contract_status_security.xml',
        'data/finance_access_groups_data.xml',
        'security/ir.model.access.csv',
        'views/product_dashboard.xml',
        'views/wave2_peg_africa_payment_views.xml',
        'views/wave2_peg_africa_views.xml',
        'views/wave2_peg_africa_purchase_views.xml',
        'views/wave2_peg_africa_crm_views.xml',
        'views/wave2_peg_africa_stock_allocation_views.xml',
        'views/traceability_report_views.xml',
        'data/api_gateway_data.xml',
        'wizard/wizard_free_day_discount.xml',
        'wizard/wizard_discount_view.xml',
    #     'security/wave2_peg_africa_security.xml',
        'views/wave2_peg_africa_invoice_stock_action.xml',
        'views/wave2_peg_africa_invoice_views.xml',
        'views/wave2_peg_africa_stock_delivery_views.xml',
    #     'data/api_gateway_token.xml',
        'views/wave2_peg_africa_credit_views.xml',
    #     'data/contract_status.xml',
        'views/wave2_peg_africa_mdm_views.xml',
        'data/master_data.xml',
        'data/automated_actions.xml'
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}