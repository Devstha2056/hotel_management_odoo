
from odoo import fields, models,api


class AccountMove(models.Model):
    _inherit = "account.move"

    hotel_booking_id = fields.Many2one(
        'room.booking',
        string="Booking Reference",
        help="Choose the Booking Reference"
    )
    booking_reference = fields.Char(string='Booking Reference', readonly=True)

