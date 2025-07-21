
from odoo import fields, models, _

class RoomBookingLineTemp(models.TransientModel):
    _name = 'room.booking.line.temp'
    _description = 'Temporary Room Booking Line'

    room_name = fields.Char(string="Room Name")
    status = fields.Selection([
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('occupied', 'Occupied'),
    ], string="Status")
    partner_id = fields.Char(string="Guest")
    checkin_date = fields.Date(string="Check-In")
    checkout_date = fields.Date(string="Check-Out")
    wizard_id = fields.Many2one('room.booking.detail', string="Wizard")
