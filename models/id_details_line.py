from odoo import api, fields, models, tools


class HotelIdDetails(models.Model):
    """Model that handles the food booking"""
    _name = "hotel.id.details.line"
    _description = "Hotel id Line"
    _rec_name = 'card_name'

    booking_id = fields.Many2one("room.booking", string="Booking",
                                 help="Shows the room Booking",
                                 ondelete="cascade")

    card_name = fields.Char('ID Card Number', required=True)

    doc_type_id = fields.Many2one("id.master", "Document Type", required=True)

    guest_name = fields.Char('Guest Name')

    issuing_auth = fields.Char('Issuing Authority', default=lambda self: self.env.user.name)

    gender = fields.Selection(
        [('M', 'Male'), ('F', 'Female'), ('O', 'Other')], 'Gender')

    valid_from = fields.Date('Valid From')

    valid_to = fields.Date('Valid To')



