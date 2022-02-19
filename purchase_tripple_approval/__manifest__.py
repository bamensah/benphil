# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.
{

    'name': 'Approval Purchase Order Tripple',
    'version': '5.13.2',
    'category': 'Inventory/Purchase',
    'license': 'Other proprietary',
    'images': ['static/description/pota.jpg'],
    'price': 99.0,
    'currency': 'EUR',
    #'live_test_url': 'https://youtu.be/YCTQ81S--4Y',
    'live_test_url': 'https://probuseappdemo.com/probuse_apps/purchase_tripple_approval/788',#'https://youtu.be/bORb4tR0-0k',
    'support': 'contact@probuse.com',
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'www.probuse.com',
    'summary': 'Approval Purchase Order Tripple: Purchase Manager -> Finance Manager -> Director Approval',
    'description' : '''
Added Finance Approval Start Range, Stop Range
Added Director Approval Start Range, Stop Range
purchase approval flow
purchase director approve
rfq
purchase finanance approve
purchase accounting approve
Director Approval
purchase account deparement approve
purchase approval
purchase approve
purchase workflow
purchase workflow approval
User Validation For Purchase
Purchase Orde limit
purchase flow
purchase management
purchase system
purchase odoo
odoo purchase
Purchase order double validation
purchase button
workflow purchase
flow purchase
approve purchase
approval purchase order
purchase order approval flow
purchase order director approve
purchase order finanance approve
purchase order accounting approve
purchase order account deparement approve
purchase order approval
purchase order approve
purchase order workflow
purchase order workflow approval
purchase order flow
purchase order management
purchase order system
purchase order odoo
odoo purchase order
purchase order button
workflow purchase order
flow purchase order
approve purchase order
Approval Purchase Order Tripple: Purchase Manager -> Finance Manager -> Director Approval.

System is flexible to have approval buttons based on amounts configured on company form. For example if purchase amount less 5000 then in only required single level approval but if amount of purchase order is greater then 5000 and less 8000 then it will need Purchase manager + Finance manager approval..

Main Features
* Added Finance Approval Start Range, Stop Range.
* Added Director Approval Start Range, Stop Range.
Menus Available:

Purchase
-- Purchase/Purchase Order Purchase/Department Approve
-- Purchase/Purchase Order Finance Approve
-- Purchase/Purchase Order Director Approve
Invoicing
-- Invoicing/Purchase/Purchase Order Finance Approve
Purchase Order Workflow Sample Example Users in Screens and Video

PO User ===> Denzel Washington
PO Purchase/Department Manager ==> Johnny Depp
PO Finance Manager ==> Robert De Niro
PO Director Manager ==> Kevin Spacey
 
''',
    'depends': ['purchase'],
    'data': [
            'security/ir.model.access.csv',
            'data/approve_mail_template.xml',
            'data/refuse_mail_template.xml',
            'security/purchase_security.xml',
            'wizard/purchase_order_refuse_wizard_view.xml',
            'views/purchase_view.xml',
            # 'views/res_company_view.xml',
            'views/res_cnfig_setting_views.xml',
             ],
    'installable': True,
    'auto_install': False
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
