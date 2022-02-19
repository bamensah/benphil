# -*- coding: utf-8 -*-
# Part of Softhealer Technologies

{
    "name": "All In One Backdate | Sale Backdate | Purchase Backdate | Accounting Backdate | Invoice Backdate | Inventory Backdate",
    "author" : "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "Extra Tools",
    "summary": "Backdate Remarks Confirmation Backdate Mass Backdate Sale order backdate Purchase order backdate custom backdate MRP order backdate Bill backdate Credit Note backdate Debit note backdate Payment backdate Picking order backdate Scrap backdate Odoo",
    "description": """Our module is useful for confirm sales, purchase, accounting, MRP & inventory orders with selected confirmation backdate. You can put a custom backdate and remarks. You can mass assign backdate in one click. This selected date and remarks are also reflects in the stock moves, product moves & journal entries.""",
    "version": "14.0.1",
    "depends": ["stock_account", "mrp", "purchase","sale_management", ],
    "data": [

        'sh_mrp_backdate/security/ir.model.access.csv',
        'sh_mrp_backdate/security/backdate_security.xml',
        'sh_mrp_backdate/wizard/mrp_backdate_wizard.xml',
        'sh_mrp_backdate/views/mrp_config_settings.xml',
        'sh_mrp_backdate/views/mrp_production.xml',
        'sh_mrp_backdate/views/stock_move.xml',
        'sh_mrp_backdate/views/stock_move_line.xml',
        'sh_mrp_backdate/views/mrp_backdate_multi_action.xml',


        'sh_purchase_backdate/security/ir.model.access.csv',
        'sh_purchase_backdate/security/backdate_security.xml',
        'sh_purchase_backdate/wizard/mass_assign_backdate_wizard.xml',
        'sh_purchase_backdate/views/purchase_config_settings.xml',
        'sh_purchase_backdate/views/purchase_order.xml',
        'sh_purchase_backdate/views/account_move.xml',
        'sh_purchase_backdate/views/stock_picking.xml',
        'sh_purchase_backdate/views/stock_move.xml',
        'sh_purchase_backdate/views/stock_move_line.xml',
        'sh_purchase_backdate/views/purchase_backdate_multi_action.xml',
        
        
        'sh_sale_backdate/security/ir.model.access.csv',
        'sh_sale_backdate/security/backdate_security.xml',
        'sh_sale_backdate/wizard/mass_assign_backdate_wizard.xml',
        'sh_sale_backdate/views/sale_config_settings.xml',
        'sh_sale_backdate/views/sale_order.xml',
        'sh_sale_backdate/views/account_move.xml',
        'sh_sale_backdate/views/stock_picking.xml',
        'sh_sale_backdate/views/stock_move.xml',
        'sh_sale_backdate/views/stock_move_line.xml',
        'sh_sale_backdate/views/sale_backdate_multi_action.xml',   


        'sh_stock_backdate/security/ir.model.access.csv',
        'sh_stock_backdate/security/backdate_security.xml',
        'sh_stock_backdate/wizard/picking_backdate_wizard.xml',
        'sh_stock_backdate/wizard/scrap_backdate_wizard.xml',
        'sh_stock_backdate/wizard/adjustment_backdate_wizard.xml',
        'sh_stock_backdate/views/stock_config_settings.xml',
        'sh_stock_backdate/views/stock_picking.xml',
        'sh_stock_backdate/views/stock_move.xml',
        'sh_stock_backdate/views/stock_inventory.xml',
        'sh_stock_backdate/views/stock_scrap.xml',
        'sh_stock_backdate/views/stock_move_line.xml',
        'sh_stock_backdate/views/stock_backdate_multi_action.xml',
        
        'sh_account_backdate/security/ir.model.access.csv',
        'sh_account_backdate/security/backdate_security.xml',
        'sh_account_backdate/wizard/invoice_backdate_wizard.xml',
        'sh_account_backdate/wizard/payment_backdate_wizard.xml',
        'sh_account_backdate/views/res_config_settings.xml',
        'sh_account_backdate/views/account_backdate_multi_action.xml',
        'sh_account_backdate/views/account_move.xml',
        'sh_account_backdate/views/account_payment.xml',

    ],

    "auto_install": False,
    "installable": True,
    "application": True,
    "images": ["static/description/background.png",],     
    "license": "OPL-1",
    "price": 90,
    "currency": "EUR" 
}
