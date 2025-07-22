from odoo import models, fields, api
from odoo.exceptions import ValidationError

class RoomShiftWizard(models.TransientModel):
    _name = 'room.shift.wizard'
    _description = 'Room Shift Wizard'

    booking_id = fields.Many2one('room.booking', string="Booking", required=True)
    current_room_id = fields.Many2one('hotel.room', string="Current Room", readonly=True)
    new_room_id = fields.Many2one('hotel.room', string="New Room", domain="[('is_room_avail', '=', True)]", required=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        booking = self.env['room.booking.line'].search([('room_id')])
        first_room_line = booking.room_line_ids[:1]

        if not first_room_line:
            raise ValidationError("No room line found in this booking.")

        res.update({
            'booking_id': booking.id,
            'current_room_id': first_room_line.room_id.id,
        })
        return res

    def action_shift_room(self):
        self.ensure_one()
        booking = self.booking_id
        first_room_line = booking.room_line_ids[:1]

        if not first_room_line:
            raise ValidationError("No room line found to shift.")

        # Old room: set available if it's reserved
        old_room = first_room_line.room_id
        if old_room.status == 'reserved':
            old_room.write({'is_room_avail': True, 'status': 'available'})

        # New room: set to reserved
        self.new_room_id.write({'is_room_avail': False, 'status': 'reserved'})

        # Update room in the booking line
        first_room_line.room_id = self.new_room_id
