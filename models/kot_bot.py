from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class HotelRestaurantKitchenOrderTickets(models.Model):
    _name = "hotel.restaurant.kitchen.order.tickets"
    _description = "Includes Hotel Restaurant Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'order_no'
    _order = 'order_no desc'

    order_no = fields.Char('KOT Number', readonly=True)

    res_no = fields.Char('Order Number')

    kot_date = fields.Date('Date')

    room_no = fields.Char('Room No', readonly=True)

    w_name = fields.Char('Waiter Name', readonly=True)

    product_nature = fields.Selection([("kot", "KOT"),
                                       ("bot", "BOT"), ], string="Product Nature",default='kot',
                                      help="Nature of Product",
                                      tracking=True)
    food_booking_kot_line_ids = fields.One2many(
        'food.booking.line',
        'kot_order_id',
        string='Food Booking Lines',
        help='Linked food items for this kitchen order'
    )
    active = fields.Boolean(string='Active', default=True)

    # @api.model
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get("order_no", "New") == "New":
    #             vals["order_no"] = self.env["ir.sequence"].next_by_code("hotel.restaurant.kitchen.order.tickets") or 'New'
    #     return super().create(vals_list)
    @api.model
    def create(self, vals):
        if not isinstance(vals, dict):
            raise ValidationError("Unexpected data format in create. Expected dictionary.")

        if vals.get('order_no', 'New') == 'New':
            vals['order_no'] = self.env['ir.sequence'].next_by_code('hotel.restaurant.kitchen.order.tickets') or '/'
        return super(HotelRestaurantKitchenOrderTickets, self).create(vals)

    def unlink(self):
        if not self.env.user.has_group('base.group_no_one'):
            raise UserError("You are not allowed to delete Restaurant Orders.")
        return super(HotelRestaurantKitchenOrderTickets, self).unlink()






class HotelRestaurantBarOrderTickets(models.Model):
    _name = "hotel.restaurant.bar.order.tickets"
    _description = "Includes Hotel Restaurant Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name='order_no'
    _order = 'order_no desc'


    order_no = fields.Char('BOT Number', readonly=True)

    res_no = fields.Char('Order Number')

    kot_date = fields.Date('Date')

    room_no = fields.Char('Room No', readonly=True)

    w_name = fields.Char('Waiter Name', readonly=True)

    product_nature = fields.Selection([("kot", "KOT"),
                                       ("bot", "BOT"), ], string="Product Nature",default='bot',
                                      help="Nature of Product",
                                      tracking=True)

    food_booking_bot_line_ids = fields.One2many(
        'food.booking.line',
        'bot_order_id',
        string='Food Booking Lines',
        help='Linked food items for this kitchen order'
    )
    active = fields.Boolean(string='Active', default=True)

    # @api.model
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get("order_no", "New") == "New":
    #             vals["order_no"] = self.env["ir.sequence"].next_by_code("hotel.restaurant.bar.order.tickets") or 'New'
    #     return super().create(vals_list)
    @api.model
    def create(self, vals):
        if not isinstance(vals, dict):
            raise ValidationError("Unexpected data format in create. Expected dictionary.")

        if vals.get('order_no', 'New') == 'New':
            vals['order_no'] = self.env['ir.sequence'].next_by_code('hotel.restaurant.bar.order.tickets') or '/'
        return super(HotelRestaurantBarOrderTickets, self).create(vals)

    def unlink(self):
        if not self.env.user.has_group('base.group_no_one'):
            raise UserError("You are not allowed to delete Restaurant Orders.")
        return super(HotelRestaurantBarOrderTickets, self).unlink()