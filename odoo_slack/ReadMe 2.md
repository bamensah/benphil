# OdooSlack

This module simply accepts message, and slack Id to perform hand-shakes between odoo and slack.  
Note that: requests library, which as of now, is not shipped with python has to be installed on the system.
`pip install requests`.  
It is currently best suited for automated actions and server action
### Example
This is an implemtation of an automated action: It sends a slack message to channel upon sent quotation
```
# Available variables:
#  - env: Odoo Environment on which the action is triggered
#  - model: Odoo Model of the record on which the action is triggered; is a void recordset
#  - record: record on which the action is triggered; may be void
#  - records: recordset of all records on which the action is triggered in multi-mode; may be void
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - Warning: Warning Exception to use with raise
# To return an action, assign: action = {...}
odoo_slack = env["odoo.slack"] # Ops team Webhook
slack_hook = "https://hooks.slack.com/services/T4EXXXXXX/BM4XXXXXX/w436XXXXXXXXXXXXXXXXXXXX" # Slack Webhook
message = '''Sales Order {0},\n {1} just placed an order worth {2}'''.format(record.name, record.partner_id.name, record.amount_total)
odoo_slack.slackup(slack_hook, message)
```
