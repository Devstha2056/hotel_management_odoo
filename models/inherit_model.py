from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError,UserError

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

    is_servicetype = fields.Boolean(default=False, string="Service Type",help="Check if the Service Type")

    floor_id=fields.Many2one('hotel.floor',string='Floor Name')

    amenity_id_group=fields.Many2one('hotel.amenity.group',string='Amenity')

    product_nature = fields.Selection([("kot", "KOT"),
                               ("bot", "BOT"),], string="Product Nature",
                              help="Nature of Product",
                              tracking=True)

    def unlink(self):
        if not self.env.user.has_group('base.group_no_one'):
            raise UserError("You are not allowed to delete Restaurant Orders.")
        return super(ProductTemplate, self).unlink()


class ProductCategory(models.Model):
    _inherit = 'product.category'

    isroomtype = fields.Boolean(string="Is Room Type")
    isfoodtype = fields.Boolean(string="Is Food Type")



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    booking_reference=fields.Char(string='Booking Reference')

    booking_id = fields.Many2one("room.booking", string="Booking",
                                 help="Indicates the Room",readonly=True,
                                 ondelete="cascade")

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({
            'booking_reference': self.booking_reference,
        })
        return invoice_vals

class ResPartner(models.Model):
    _inherit = 'res.partner'

    isagenttype = fields.Boolean(string="Is Agent Type")