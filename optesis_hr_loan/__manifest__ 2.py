{
    'name': 'Hr Loan',
    'version': '12.0.8',
    'author': 'Mouhamadou Yacine DIallo',
    'category': 'Human Resources',
    'description': """

	""",

    'depends': ['hr', 'hr_payroll', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_loan_notification.xml',
        'wizard/hr_loan_action_refusal.xml',
        'views/hr_loan_view.xml',
        'views/hr_payroll_view.xml',
    ],

    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
