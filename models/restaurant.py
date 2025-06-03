from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class RestaurantOrder(models.Model):
    _name = "restaurant.order"
    _description = 'Hotel Restaurant order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    order_no = fields.Char('Order Number', readonly=True)
    name = fields.Char('Name')
    room_no = fields.Many2one('room.booking.line', 'Room No', domain="[('state', '=', 'check_in')]", required=True)
    partner_id = fields.Many2one(related='room_no.customer')
    guest_name = fields.Char('Guest Name')
    o_date = fields.Datetime('Date', required=True, default=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    waiter_name = fields.Many2one('res.partner', 'Waiter Name')

    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('done', 'Done'),
                              ('order', 'Order Done'),
                              ('cancel', 'Cancelled')],
                             string='State', default='draft', index=True, required=True)

    folio_ids = fields.Many2one('room.booking', string='Booking Reference')

    food_order_restaurant_line_ids = fields.One2many('food.booking.line','restaurant_order_id',
                                                     string='Restaurant Order Line',help='Linked food items for this kitchen order' )

    active = fields.Boolean(string='Active', default=True)

    @api.onchange('room_no')
    def _onchange_room_no_set_folio_id(self):
        for rec in self:
            if rec.room_no and rec.room_no.booking_id:
                rec.folio_ids = rec.room_no.booking_id
            else:
                rec.folio_ids = False

    #
    # @api.model
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if vals.get('order_no', 'New') == 'New':
    #             vals['order_no'] = self.env['ir.sequence'].next_by_code('restaurant.order') or 'New'
    #     return super(RestaurantOrder, self).create(vals_list)
    @api.model
    def create(self, vals):
        if not isinstance(vals, dict):
            raise ValidationError("Unexpected data format in create. Expected dictionary.")

        if vals.get('order_no', 'New') == 'New':
            vals['order_no'] = self.env['ir.sequence'].next_by_code('restaurant.order') or '/'
        return super(RestaurantOrder, self).create(vals)

    def action_confirm(self):
        for record in self:
            record.state = 'confirm'

    def action_cancel(self):
        for record in self:
            record.state = 'cancel'

    def action_order_done(self):
        for record in self:
            record.state = ('order'
                            '')
            if record.food_order_restaurant_line_ids:
                food_order = self.env['room.booking'].search([ ('id', '=', record.folio_ids.id)], limit=1)
                if food_order:
                    food_order.food_order_line_ids = [(4, line.id) for line in record.food_order_restaurant_line_ids]

    def unlink(self):

        if not self.env.user.has_group('base.group_no_one'):
            raise UserError("You are not allowed to delete Restaurant Orders.")
        return super(RestaurantOrder, self).unlink()

    def action_create_kot_bot_orders(self):
        for record in self:
            record.state = 'done'
            # Split lines based on product_nature
            kot_lines = record.food_order_restaurant_line_ids.filtered(lambda l: l.product_nature == 'kot')
            bot_lines = record.food_order_restaurant_line_ids.filtered(lambda l: l.product_nature == 'bot')

            created_orders = {}

            # Create KOT
            if kot_lines:
                order = kot_lines[0].restaurant_order_id
                kot_order = self.env['hotel.restaurant.kitchen.order.tickets'].create({
                    'res_no': order.order_no or '',
                    'kot_date': fields.Date.today(),
                    'room_no': order.room_no.display_name or '',
                    'w_name': order.waiter_name.display_name or '',
                    'product_nature': 'kot',
                    'food_booking_kot_line_ids': [(6, 0, kot_lines.ids)]
                })
                kot_lines.write({'kot_order_id': kot_order.id})
                created_orders['kot'] = kot_order

            # Create BOT
            if bot_lines:
                order = bot_lines[0].restaurant_order_id
                bot_order = self.env['hotel.restaurant.bar.order.tickets'].create({
                    'res_no': order.order_no or '',
                    'kot_date': fields.Date.today(),
                    'room_no': order.room_no.display_name or '',
                    'w_name': order.waiter_name.display_name or '',
                    'product_nature': 'bot',
                    'food_booking_bot_line_ids': [(6, 0, bot_lines.ids)]
                })
                bot_lines.write({'bot_order_id': bot_order.id})
                created_orders['bot'] = bot_order

            _logger.info(f'============={created_orders}==============================')

            if not created_orders:
                raise UserError("No KOT or BOT items found to create an order.")

        return created_orders
