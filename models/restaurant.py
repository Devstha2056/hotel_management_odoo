from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class RestaurantOrder(models.Model):
    _name = "restaurant.order"
    _description = 'Hotel Restaurant order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'order_no desc'

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
    currency_id = fields.Many2one('res.currency', string='Currency')

    food_order_restaurant_line_ids = fields.One2many('food.booking.line','restaurant_order_id',
                                                     string='Restaurant Order Line',help='Linked food items for this kitchen order' )
    amount_untaxed_food = fields.Monetary(string="Food Taxable",
                                          help="Untaxed Amount for Food",
                                          compute='_compute_amount_untaxed',
                                          tracking=5)
    amount_taxed_food = fields.Monetary(string="Food Tax", help="Tax for Food",
                                        compute='_compute_amount_untaxed',
                                        tracking=5)
    amount_total_food = fields.Monetary(string="Total Amount for Food",
                                        compute='_compute_amount_untaxed',
                                        help="This is the Total Amount for "
                                             "Food", tracking=5)
    active = fields.Boolean(string='Active', default=True)

    @api.onchange('room_no')
    def _onchange_room_no_set_folio_id(self):
        for rec in self:
            if rec.room_no and rec.room_no.booking_id:
                rec.folio_ids = rec.room_no.booking_id
            else:
                rec.folio_ids = False

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


    def _compute_amount_untaxed(self, flag=False):
        """Compute the total amounts of the Sale Order"""
        amount_untaxed_food = 0.0
        amount_taxed_food = 0.0
        amount_total_food = 0.0

        food_lines = self.food_order_restaurant_line_ids

        booking_list = []
        account_move_line = self.env['account.move.line'].search_read(
            domain=[('ref', '=', self.name),
                    ('display_type', '!=', 'payment_term')],
            fields=['name', 'quantity', 'price_unit', 'product_type'], )
        for rec in account_move_line:
            del rec['id']

        if food_lines:
            for food in food_lines:
                booking_list.append(self.create_list(food))
            amount_untaxed_food += sum(food_lines.mapped('price_subtotal'))
            amount_taxed_food += sum(food_lines.mapped('price_tax'))
            amount_total_food += sum(food_lines.mapped('price_total'))

        for rec in self:
            rec.amount_untaxed_food = amount_untaxed_food
            rec.amount_taxed_food = amount_taxed_food
            rec.amount_total_food = amount_total_food
        return booking_list
    
    def create_list(self, line_ids):
        """Returns a List of Dictionaries for Booking Lines"""
        booking_list = []
        for line in line_ids:
            model_name = line._name
            name = ""
            product_type = ""
            product_id = None

            if model_name == 'room.booking.line':
                name = line.room_id.name
                product_id = line.room_id.id
                product_type = 'room'
            elif model_name == 'food.booking.line':
                name = line.food_id.name
                product_id = line.food_id.id
                product_type = 'food'
            elif model_name == 'fleet.booking.line':
                name = line.fleet_id.name
                product_id = line.fleet_id.id
                product_type = 'fleet'
            elif model_name == 'service.booking.line':
                name = line.service_id.name
                product_id = line.service_id.id
                product_type = 'service'
            elif model_name == 'event.booking.line':
                name = line.event_id.name
                product_id = line.event_id.id
                product_type = 'event'
            else:
                continue  # Unknown model

            # Check for missing product
            if not product_id:
                raise ValidationError("Product is missing in one of the booking lines.")

            booking_list.append({
                'name': name,
                'quantity': line.uom_qty,
                'price_unit': line.price_unit,
                'discount': getattr(line, 'discount', 0.0),
                'product_type': product_type,
                'product_id': product_id,
            })

        return booking_list

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
