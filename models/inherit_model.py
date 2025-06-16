from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError,UserError
import odoo.addons.decimal_precision as dp


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
    room_line_ids = fields.One2many("room.booking.line",
                                    "room_id", string="Room",
                                    help="Hotel room reservation detail.")

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



    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = amount_discount = amount_subtotal = 0.0
            for line in order.order_line:

                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amount_discount += (line.product_uom_qty * line.price_unit * line.discount) / 100
                amount_subtotal += (line.price_subtotal + amount_discount)
            order.update({
                'amount_untaxed': amount_untaxed,
                'amount_tax': amount_tax,
                'amount_discount': amount_discount,
                'amount_subtotal':amount_subtotal,
                'amount_total': amount_untaxed + amount_tax,
            })


    amount_untaxed = fields.Monetary(string='Taxable Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always')

    amount_subtotal = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always')


    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all',
                                 track_visibility='always')

    amount_total = fields.Monetary(string=' Grand Total', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')
    amount_discount = fields.Monetary(string='Discount Amount', store=True, readonly=True, compute='_amount_all',
                                      digits=dp.get_precision('Account'), track_visibility='always')

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({
            'booking_reference': self.booking_reference,
        })
        return invoice_vals

class ResPartner(models.Model):
    _inherit = 'res.partner'

    isagenttype = fields.Boolean(string="Is Agent Type")

