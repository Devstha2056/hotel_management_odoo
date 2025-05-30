from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    status = fields.Selection([("available", "Available"),
                               ("reserved", "Reserved"),
                               ("occupied", "Occupied")],
                              default="available", string="Status",
                              help="Status of The Room",
                              tracking=True)

    is_room_avail = fields.Boolean(default=True, string="Available",help="Check if the room is available")

    is_roomtype = fields.Boolean(default=False, string="Room Type",help="Check if the RoomType")

    is_foodtype = fields.Boolean(default=False, string="Food Type",help="Check if the FoodType")

    floor_id=fields.Many2one('hotel.floor',string='Floor Name')

    amenity_id_group=fields.Many2one('hotel.amenity.group',string='Amenity')

    product_nature = fields.Selection([("kot", "KOT"),
                               ("bot", "BOT"),], string="Product Nature",
                              help="Nature of Product",
                              tracking=True)



class ProductCategory(models.Model):
    _inherit = 'product.category'

    isroomtype = fields.Boolean(string="Is Room Type")
    isfoodtype = fields.Boolean(string="Is Food Type")



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    booking_reference=fields.Char(string='Booking Reference')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    isagenttype = fields.Boolean(string="Is Agent Type")