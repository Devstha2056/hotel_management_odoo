
from odoo import fields, models,api


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    product_type = fields.Selection([('room', 'Room'),
                                     ('food', 'Food'),
                                     ('event', 'Event'),
                                     ('service', 'Service'),
                                     ('fleet', 'Fleet')],
                                    string="Product Type",
                                    help="Choose the product type")


