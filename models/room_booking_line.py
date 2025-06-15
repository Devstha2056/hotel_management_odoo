from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError,UserError
from datetime import datetime,time,timedelta,date
import logging
import pytz
logger = logging.getLogger(__name__)

class RoomBookingLine(models.Model):
    """Model that handles the room booking form"""
    _name = "room.booking.line"
    _description = "Hotel Folio Line"
    _rec_name = 'room_id'
    _order = 'booking_ref desc'

    @tools.ormcache()
    def _set_default_uom_id(self):
        return self.env.ref('uom.product_uom_day')

    booking_id = fields.Many2one("room.booking", string="Booking",
                                 help="Indicates the Room",
                                 ondelete="cascade")


    customer = fields.Many2one('res.partner', related='booking_id.partner_id', store=True, readonly=True,
                               ondelate='cascade')
    phone_id = fields.Char(related='booking_id.phone_id', string='Mobile', readonly=False, required=True,help="Phone Number of Customer")

    booking_ref = fields.Char(related='booking_id.name', store=True, readonly=True)

    today_date=fields.Date(string='Today' ,default=fields.Date.today)

    checkin_date = fields.Datetime(string="Check In",
                                   help="You can choose the date,"
                                        " Otherwise sets to current Date",
                                   required=True,tracking=True)
    checkout_date = fields.Datetime(string="Check Out",
                                    help="You can choose the date,"
                                         " Otherwise sets to current Date",
                                    required=True,tracking=True)

    hotel_id = fields.Many2one('hotel.plan', string='Hotel Plan')

    meal_plan_price = fields.Float(string="Meal Plan Price", compute="_compute_price", store=True,tracking=True)

    meal_plan_ids = fields.Many2one(related='hotel_id.meal_plan_id', string="Meal Plan",store=True, readonly=False, required=True,tracking=True)

    occupancy_id = fields.Selection(related='hotel_id.occupancy', string='Occupancy',store=True, readonly=False,required=True,tracking=True)

    categ_id = fields.Many2one('product.category', string='Category', domain="[('isroomtype','=',True)]",tracking=True)

    room_id = fields.Many2one('product.product',string='Room',domain="[('is_roomtype','=',True),('categ_id', '=', categ_id)]",tracking=True)

    uom_qty = fields.Float(string="Duration", help="The quantity converted into the UoM used by " "the product",
                           readonly=True, compute='_onchange_checkin_date')

    uom_id = fields.Many2one('uom.uom',
                             default=_set_default_uom_id,
                             string="Unit of Measure",
                             help="This will set the unit of measure used",
                             readonly=True)

    price_unit = fields.Float(string='Rent',
                              digits='Product Price',
                              help="The rent price of the selected room.")

    tax_ids = fields.Many2many('account.tax',
                               'hotel_room_order_line_taxes_rel',
                               'room_id', 'tax_id',
                               related='room_id.taxes_id',
                               string='Taxes',
                               help="Default taxes used when selling the room."
                               , domain=[('type_tax_use', '=', 'sale')])

    currency_id = fields.Many2one(string='Currency',
                                  related='booking_id.pricelist_id.currency_id'
                                  , help='The currency used')
    price_subtotal = fields.Float(string="Subtotal",
                                  compute='_compute_price_subtotal',
                                  help="Total Price excluding Tax",
                                  )

    price_tax = fields.Float(string="Total Tax",
                             compute='_compute_price_subtotal',
                             help="Tax Amount",
                             store=True)
    price_total = fields.Float(string="Total",
                               compute='_compute_price_subtotal',
                               help="Total Price including Tax",
                               )
    state = fields.Selection(related='booking_id.state',
                             string="Order Status",
                             help=" Status of the Order",
                             copy=False)

    booking_line_visible = fields.Boolean(default=False,
                                          string="Booking Line Visible",
                                          help="If True, then Booking Line "
                                               "will be visible")

    discount = fields.Float(string="Discount (%)", default=0.0)

    today = fields.Date(string='Today', compute='_compute_today')

    active = fields.Boolean(string='Active', default=True)

    def _compute_today(self):
        for record in self:
            record.today = fields.Date.context_today(self)

    @api.depends('occupancy_id', 'meal_plan_ids', 'categ_id','room_id')
    def _compute_price(self):
        for rec in self:
            rec.meal_plan_price = 0.0  # Always assign something to avoid compute error

            if rec.categ_id and rec.meal_plan_ids and rec.occupancy_id:
                rule = self.env['hotel.plan'].search([
                    ('cat_id', '=', rec.categ_id.id),
                    ('meal_plan_id', '=', rec.meal_plan_ids.id),
                    ('occupancy', '=', rec.occupancy_id),
                ], limit=1)

                if rule:
                    rec.meal_plan_price = rule.price

    @api.onchange('occupancy_id', 'meal_plan_ids', 'categ_id','room_id')
    def onchange_compute_price(self):
        self._compute_price()

    @api.onchange('occupancy_id', 'meal_plan_ids', 'categ_id','room_id')
    def _get_list_price(self):
        for line in self:
            if line.room_id:
                addons=line.meal_plan_price
                line.price_unit = addons
                logger.info(f'===========aaaaaaaaa=={line.price_unit}==========')
                line.tax_ids = line.room_id.taxes_id

    @api.onchange("checkin_date", "checkout_date")
    def _onchange_checkin_date(self):
        for record in self:
            if record.checkin_date and record.checkout_date:
                if record.checkout_date < record.checkin_date:
                    raise ValidationError(
                        _("Checkout must be greater or equal to check-in date"))
                diffdate = record.checkout_date - record.checkin_date
                qty = diffdate.days
                if diffdate.total_seconds() > 0:
                    qty += 1
                record.uom_qty = qty
    @api.onchange("uom_qty")
    def _onchange_uom_qty(self):
        for line in self:
            if line.price_unit and line.uom_qty:
                base_line = line.env['account.tax']._prepare_base_line_for_taxes_computation(
                    line,
                    **{
                        'price_unit': line.price_unit,
                        'quantity': line.uom_qty,
                        'currency_id': line.currency_id,
                        'product': line.room_id,
                        'discount': line.discount,
                        'partner': line.booking_id.partner_id,
                        'tax_ids': line.tax_ids,
                    }
                )
                line.env['account.tax']._add_tax_details_in_base_line(base_line, line.env.company)

                line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
                line.price_total = base_line['tax_details']['raw_total_included_currency']
                line.price_tax = line.price_total - line.price_subtotal

    @api.depends('uom_qty', 'price_unit', 'tax_ids', 'discount')
    def _compute_price_subtotal(self):
        """Compute the amounts of the room booking line with discount."""
        for line in self:
            base_line = line.env['account.tax']._prepare_base_line_for_taxes_computation(
                line,
                **{
                    'price_unit': line.price_unit,
                    'quantity': line.uom_qty,
                    'currency_id': line.currency_id,
                    'product': line.room_id,
                    'discount': line.discount,
                    'partner': line.booking_id.partner_id,
                    'tax_ids': line.tax_ids,
                }
            )

            line.env['account.tax']._add_tax_details_in_base_line(base_line, line.env.company)

            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            line.price_total = base_line['tax_details']['raw_total_included_currency']
            line.price_tax = line.price_total - line.price_subtotal

    def _prepare_base_line_for_taxes_computation(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            **{
                'tax_ids': self.tax_ids,
                'quantity': self.uom_qty,
                'discount': self.discount or 0.0,
                'partner_id': self.booking_id.partner_id,
                'currency_id': self.currency_id,
            },
        )

    @api.onchange('checkin_date', 'checkout_date', 'room_id')
    def onchange_checkin_date(self):
        for line in self:
            if not line.room_id or not line.checkin_date or not line.checkout_date:
                continue

            if line.checkout_date <= line.checkin_date:
                raise ValidationError(_("Checkout date must be after check-in date."))

            # Search for overlapping bookings for the same room
            overlapping_bookings = self.env['room.booking.line'].search([
                ('id', '!=', line.id),  # Exclude the current line
                ('room_id', '=', line.room_id.id),
                ('booking_id.state', 'in', ['reserved', 'check_in']),
                '|',
                '&',
                ('checkin_date', '<=', line.checkin_date),
                ('checkout_date', '>=', line.checkin_date),
                '&',
                ('checkin_date', '<=', line.checkout_date),
                ('checkout_date', '>=', line.checkout_date),
            ])

            if overlapping_bookings:
                raise ValidationError(_(
                    "Sorry, the room is already reserved or checked in between these dates."
                ))

    @api.constrains('checkin_date', 'checkout_date', 'room_id')
    def _check_room_availability(self):
        for line in self:
            overlapping = self.env['room.booking.line'].search([
                ('id', '!=', line.id),
                ('room_id', '=', line.room_id.id),
                ('booking_id.state', 'in', ['reserved', 'check_in']),
                '|',
                '&', ('checkin_date', '<=', line.checkin_date), ('checkout_date', '>=', line.checkin_date),
                '&', ('checkin_date', '<=', line.checkout_date), ('checkout_date', '>=', line.checkout_date),
            ])
            if overlapping:
                raise ValidationError(_("Room is not available for the selected dates."))

    @api.onchange('checkin_date')
    def _onchange_checkin_set_time(self):
        user_tz = self.env.user.tz or 'UTC'
        tz = pytz.timezone(user_tz)
        for rec in self:
            if rec.checkin_date:
                # Build a datetime with 2:00 PM in user's timezone
                local_dt = tz.localize(datetime.combine(rec.checkin_date.date(), time(14, 0)))
                # Convert to UTC
                utc_dt = local_dt.astimezone(pytz.utc)
                # Make it naive (strip timezone info)
                rec.checkin_date = utc_dt.replace(tzinfo=None)

    @api.onchange('checkout_date')
    def _onchange_checkout_set_time(self):
        user_tz = self.env.user.tz or 'UTC'
        tz = pytz.timezone(user_tz)
        for rec in self:
            if rec.checkout_date:
                local_dt = tz.localize(datetime.combine(rec.checkout_date.date(), time(12, 0)))
                utc_dt = local_dt.astimezone(pytz.utc)
                rec.checkout_date = utc_dt.replace(tzinfo=None)

    def unlink(self):
        for rec in self:
            if rec.room_id:
                rec.room_id.status = 'available'
        if not self.env.user.has_group('base.group_no_one'):
            raise UserError("You are not allowed to delete Restaurant Orders.")
        for line in self:
            if line.booking_id:
                line.booking_id.message_post(
                    body=f"Room Deleted:{line.room_id.name}"
                )
        return super(RoomBookingLine, self).unlink()

