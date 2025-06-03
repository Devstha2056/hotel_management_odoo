from odoo import fields, models
from odoo.exceptions import ValidationError, UserError

class HotelAmenity(models.Model):
    _name = 'hotel.amenity'
    _description = "Hotel Amenity"
    _inherit = 'mail.thread'
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(string='Name', help="Name of the amenity")
    icon = fields.Image(string="Icon", help="Image of the amenity")
    description = fields.Html(string="About", help="Specify the amenity description")
    active = fields.Boolean(string='Active', default=True)


    def unlink(self):
        if not self.env.user.has_group('base.group_no_one'):
            raise UserError("You are not allowed to delete Restaurant Orders.")
        return super(HotelAmenity, self).unlink()


class HotelAmenityGroup(models.Model):
    _name = 'hotel.amenity.group'
    _description = "Hotel Amenity Group"
    _inherit = 'mail.thread'


    name = fields.Char(string='Group Name', help="Name of the Group")
    active = fields.Boolean(string='Active', default=True)
    amenity_id = fields.Many2many('hotel.amenity', string="Amenities")


    def unlink(self):
        if not self.env.user.has_group('base.group_no_one'):
            raise UserError("You are not allowed to delete Restaurant Orders.")
        return super(HotelAmenityGroup, self).unlink()






