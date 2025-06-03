from odoo import fields, models
from odoo.exceptions import ValidationError, UserError

class HotelFloor(models.Model):
    """Model that holds the Hotel Floors."""
    _name = "hotel.floor"
    _description = "Floor"
    _order = 'id desc'
    _rec_name='name'

    name = fields.Char(string="Name", help="Name of the floor", required=True)
    active = fields.Boolean(string='Active', default=True)

    user_id = fields.Many2one('res.users', string='Manager',
                              help="Manager of the Floor",
                              required=True)

    def unlink(self):
        if not self.env.user.has_group('base.group_no_one'):
            raise UserError("You are not allowed to delete Restaurant Orders.")
        return super(HotelFloor, self).unlink()
