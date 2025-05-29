from odoo import fields, models


class HotelAmenity(models.Model):
    _name = 'hotel.amenity'
    _description = "Hotel Amenity"
    _inherit = 'mail.thread'
    _order = 'id desc'
    _rec_name = 'name'

    name = fields.Char(string='Name', help="Name of the amenity")
    icon = fields.Image(string="Icon", required=True, help="Image of the amenity")
    description = fields.Html(string="About", help="Specify the amenity description")


class HotelAmenityGroup(models.Model):
    _name = 'hotel.amenity.group'
    _description = "Hotel Amenity Group"
    _inherit = 'mail.thread'


    name = fields.Char(string='Group Name', help="Name of the Group")

    amenity_id = fields.Many2many('hotel.amenity', string="Amenities")






