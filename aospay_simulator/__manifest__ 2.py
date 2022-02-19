{
    'name': 'aospay Simulator',
    'version': '12.0.3',
    'summary': 'Compute Brut salary from net',
    'description': 'Use mathematical theorie to compute the brut',
    'category': 'payroll',
    'author': 'AOS',
    'website': 'aos-solutions.odoo.com',
    'depends': ['hr_payroll', 'aospay'],
    'data': ['security/ir.model.access.csv',
             'views/simulator_views.xml',
             'views/livredepaieview.xml',
             'data/aospay_simulator_sequence.xml'
             ],
    'installable': True,
    'auto_install': False
}
