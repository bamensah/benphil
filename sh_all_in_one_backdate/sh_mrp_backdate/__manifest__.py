# -*- coding: utf-8 -*-
# Part of Softhealer Technologies

{
    "name": "MRP Backdate",
    "author" : "Softhealer Technologies",
    "website": "https://www.softhealer.com",
    "support": "support@softhealer.com",
    "category": "",
    "summary": "",
    "version": "14.0.1",
    "depends": ["stock_account","mrp"],
    "data": [
        
        'security/ir.model.access.csv',
        'security/backdate_security.xml',
        'wizard/mrp_backdate_wizard.xml',
        'views/mrp_config_settings.xml',
        'views/mrp_production.xml',
        'views/stock_move.xml',
        'views/stock_move_line.xml',
        'views/mrp_backdate_multi_action.xml',

    ],

    "images": ["",],  
    "live_test_url": "",            
    "auto_install":False,
    "installable": True,
    "application" : True,
    "price": 20,
    "currency": ""    
} 
