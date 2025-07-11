from datetime import datetime, timedelta, date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools.safe_eval import pytz
import logging

_logger = logging.getLogger(__name__)


class RoomBooking(models.Model):
    """Model that handles the hotel room booking and all operations related
     to booking"""
    _name = "room.booking"
    _description = "Hotel Room Reservation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'


    name = fields.Char(string="Folio Number", readonly=True, index=True,
                       default="New", help="Name of Folio")
    issuing_auth = fields.Char('Sale Person', default=lambda self: self.env.user.name)

    quotation_state = fields.Selection(
        related='sale_order_id.state',
        string="Order Status",
        help="Status of the Order",
        store=True  # <-- ADD THIS
    )

    company_id = fields.Many2one('res.company', string="Company",
                                 help="Choose the Company",
                                 required=True, index=True,
                                 default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 help="Customers of hotel",
                                 required=True, index=True, tracking=1,
                                 domain="[('type', '!=', 'private'),"
                                        " ('company_id', 'in', "
                                        "(False, company_id))]")
    # customaddons

    meal_plan_ids = fields.Many2one(related='room_line_ids.meal_plan_ids', string="Meal Plan", ondelate='cascade')

    email_id = fields.Char(related='partner_id.email', string='Email', readonly=False, help="Email of Customer")

    phone_id = fields.Char(related='partner_id.phone', string='Mobile', readonly=False, required=True,
                           help="Phone Number of Customer")
    street_id = fields.Char(related='partner_id.street', string='Street', readonly=False, required=True,
                            help="Street of Customer")
    city_id = fields.Char(related='partner_id.city', string='City', readonly=False,help="City of Customer")

    country_id = fields.Many2one('res.country',string="Country", help="Country Name",store=True)

    company_type = fields.Selection(related='partner_id.company_type',readonly=False, string='Company Type', store=True)

    pan_id = fields.Char(related='partner_id.vat', string='PAN', readonly=False, required=False,
                         help="PAN no. of Company")
    adults = fields.Integer(string='Pax', required=True, default=1,help="Number of Adults")

    child = fields.Integer(string='Child', help="Number of Children")

    note = fields.Text(string='Note', help="Write some of Note")

    via = fields.Selection([
        ('fit', "FIT"),
        ('agent', 'Agent'),
        ('company', 'Company'),

    ], string='Via', required=True, default='fit')

    agent_id = fields.Many2one('res.partner', string='Agent', readonly=True, domain="[('isagenttype','=',True)]")
    company_agent_id = fields.Many2one('res.partner', string='Company Agent', readonly=True,
                                       domain="[('isagenttype','=',True)]")

    source = fields.Selection([
        ('internal_reservation', "Internal Reservation"),
        ('through_web', 'Through web'),
        ('through_gds', 'Through GDS'),
    ], string='Source')

    date_order = fields.Datetime(string="Order Date",
                                 required=True, copy=False,
                                 help="Creation date of draft/sent orders,"
                                      " Confirmation date of confirmed orders",
                                 default=fields.Datetime.now)

    is_checkin = fields.Boolean(default=False, string="Is Checkin",
                                help="sets to True if the room is occupied")
    maintenance_request_sent = fields.Boolean(default=False,
                                              string="Maintenance Request sent"
                                                     "or Not",
                                              help="sets to True if the "
                                                   "maintenance request send "
                                                   "once")
    checkin_date = fields.Datetime(string="Check In",
                                   help="Date of Checkin",
                                   default=fields.Datetime.now())

    checkout_date = fields.Datetime(string="Check Out",
                                    help="Date of Checkout",
                                    default=fields.Datetime.now() + timedelta(
                                        hours=23, minutes=59, seconds=59))

    hotel_policy = fields.Selection([("prepaid", "On Booking"),
                                     ("manual", "On Check In"),
                                     ("picking", "On Checkout"),
                                     ],
                                    default="manual", string="Hotel Policy",
                                    help="Hotel policy for payment that "
                                         "either the guest has to pay at "
                                         "booking time, check-in "
                                         "or check-out time.", tracking=True)
    duration = fields.Integer(string="Duration in Days",
                              help="Number of days which will automatically "
                                   "count from the check-in and check-out "
                                   "date.", )
    invoice_button_visible = fields.Boolean(string='Invoice Button Display',
                                            help="Invoice button will be "
                                                 "visible if this button is "
                                                 "True")
    invoice_status = fields.Selection(
        selection=[('no_invoice', 'Nothing To Invoice'),
                   ('to_invoice', 'To Invoice'),
                   ('invoiced', 'Invoiced'),
                   ], string="Invoice Status",
        help="Status of the Invoice",
        default='no_invoice', tracking=True)

    hotel_invoice_id = fields.Many2one("account.move",
                                       string="Invoice",
                                       help="Indicates the invoice",
                                       copy=False)

    sale_order_id = fields.Many2one("sale.order",
                                    string="Sale Order",
                                    help="Indicates the Sale",
                                    copy=False)

    duration_visible = fields.Float(string="Duration",
                                    help="A dummy field for Duration")
    need_service = fields.Boolean(default=False, string="Need Service",
                                  help="Check if a Service to be added with"
                                       " the Booking")
    need_fleet = fields.Boolean(default=False, string="Need Vehicle",
                                help="Check if a Fleet to be"
                                     " added with the Booking")
    need_food = fields.Boolean(default=False, string="Need Food",
                               help="Check if a Food to be added with"
                                    " the Booking")
    need_event = fields.Boolean(default=False, string="Need Event",
                                help="Check if a Event to be added with"
                                     " the Booking")
    service_line_ids = fields.One2many("service.booking.line",
                                       "booking_id",
                                       string="Service",
                                       help="Hotel services details provided to"
                                            "Customer and it will included in "
                                            "the main Invoice.")
    event_line_ids = fields.One2many("event.booking.line",
                                     'booking_id',
                                     string="Event",
                                     help="Hotel event reservation detail.")
    vehicle_line_ids = fields.One2many("fleet.booking.line",
                                       "booking_id",
                                       string="Vehicle",
                                       help="Hotel fleet reservation detail.")

    room_line_ids = fields.One2many("room.booking.line",
                                    "booking_id", string="Room",
                                    help="Hotel room reservation detail.")

    active = fields.Boolean(string='Active', default=True)
    # New field added
    room_checkin_date = fields.Datetime(
        string="Check-In", compute="_compute_checkin_checkout_dates", store=True
    )
    room_checkout_date = fields.Datetime(
        string="Check-Out", compute="_compute_checkin_checkout_dates", store=True
    )

    card_name_line_ids = fields.One2many("hotel.id.details.line",
                                         "booking_id", string="ID Details",
                                         help="Hotel room reservation ID detail.")
    food_order_line_ids = fields.One2many("food.booking.line",
                                          "room_booking_id",
                                          string='Food',
                                          help="Food details provided"
                                               " to Customer and"
                                               " it will included in the "
                                               "main invoice.", )

    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('reserved', 'Reserved'),
                                        ('check_in', 'Check In'),
                                        ('check_out', 'Check Out'),
                                        ('cancel', 'Cancelled'),
                                        ('done', 'Done')], string='State',
                             help="State of the Booking",
                             default='draft', tracking=True)

    user_id = fields.Many2one(comodel_name='res.partner',
                              string="Invoice Address",
                              compute='_compute_user_id',
                              help="Sets the User automatically",
                              required=True,
                              domain="['|', ('company_id', '=', False), "
                                     "('company_id', '=',"
                                     " company_id)]")
    pricelist_id = fields.Many2one(comodel_name='product.pricelist',
                                   string="Pricelist",
                                   compute='_compute_pricelist_id',
                                   store=True, readonly=False,
                                   required=True,
                                   tracking=1,
                                   help="If you change the pricelist,"
                                        " only newly added lines"
                                        " will be affected.")
    currency_id = fields.Many2one(
        string="Currency", help="This is the Currency used",
        related='pricelist_id.currency_id',
        depends=['pricelist_id.currency_id'],
    )
    invoice_count = fields.Integer(compute='_compute_invoice_count',
                                   string="Invoice "
                                          "Count",
                                   help="The number of invoices created")
    account_move = fields.Integer(string='Invoice Id',
                                  help="Id of the invoice created")
    amount_untaxed = fields.Monetary(string="Total Untaxed Amount",
                                     help="This indicates the total untaxed "
                                          "amount", store=True,
                                     compute='_compute_amount_untaxed',
                                     tracking=5)
    amount_tax = fields.Monetary(string="Taxes", help="Total Tax Amount",
                                 store=True, compute='_compute_amount_untaxed')
    amount_total = fields.Monetary(string="Total", store=True,
                                   help="The total Amount including Tax",
                                   compute='_compute_amount_untaxed',
                                   tracking=4)
    amount_untaxed_room = fields.Monetary(string="Room Taxable",
                                          help="Untaxed Amount for Room",
                                          compute='_compute_amount_untaxed',
                                          tracking=5)
    amount_untaxed_food = fields.Monetary(string="Food Taxable",
                                          help="Untaxed Amount for Food",
                                          compute='_compute_amount_untaxed',
                                          tracking=5)
    amount_untaxed_event = fields.Monetary(string="Event Taxable",
                                           help="Untaxed Amount for Event",
                                           compute='_compute_amount_untaxed',
                                           tracking=5)
    amount_untaxed_service = fields.Monetary(
        string="Service Taxable", help="Taxable Amount for Service",
        compute='_compute_amount_untaxed', tracking=5)

    amount_untaxed_fleet = fields.Monetary(string="Amount Untaxed",
                                           help="Untaxed amount for Fleet",
                                           compute='_compute_amount_untaxed',
                                           tracking=5)
    amount_taxed_room = fields.Monetary(string="Rom Tax", help="Tax for Room",
                                        compute='_compute_amount_untaxed',
                                        tracking=5)
    amount_taxed_food = fields.Monetary(string="Food Tax", help="Tax for Food",
                                        compute='_compute_amount_untaxed',
                                        tracking=5)
    amount_taxed_event = fields.Monetary(string="Event Tax",
                                         help="Tax for Event",
                                         compute='_compute_amount_untaxed',
                                         tracking=5)
    amount_taxed_service = fields.Monetary(string="Service Tax",
                                           compute='_compute_amount_untaxed',
                                           help="Tax for Service", tracking=5)
    amount_taxed_fleet = fields.Monetary(string="Fleet Tax",
                                         compute='_compute_amount_untaxed',
                                         help="Tax for Fleet", tracking=5)
    amount_total_room = fields.Monetary(string="Total Amount for Room",
                                        compute='_compute_amount_untaxed',
                                        help="This is the Total Amount for "
                                             "Room", tracking=5)
    amount_total_food = fields.Monetary(string="Total Amount for Food",
                                        compute='_compute_amount_untaxed',
                                        help="This is the Total Amount for "
                                             "Food", tracking=5)
    amount_total_event = fields.Monetary(string="Total Amount for Event",
                                         compute='_compute_amount_untaxed',
                                         help="This is the Total Amount for "
                                              "Event", tracking=5)

    amount_total_service = fields.Monetary(string="Total Amount for Service",
                                           compute='_compute_amount_untaxed',
                                           help="This is the Total Amount for "
                                                "Service", tracking=5)
    amount_total_fleet = fields.Monetary(string="Total Amount for Fleet",
                                         compute='_compute_amount_untaxed',
                                         help="This is the Total Amount for "
                                              "Fleet", tracking=5)

    total_quotation = fields.Integer(string='Quotation Count', compute='confirmed_count')

    @api.depends('name','sale_order_id.state')
    def confirmed_count(self):
        for record in self:
            confirmed_total = self.env['sale.order'].search_count([
                ('booking_reference', '=', record.name),
                ('state', 'in', ['sale', 'cancel']),
            ])
            record.total_quotation = confirmed_total

    def action_open_quotations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quotations',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [
                ('booking_reference', '=', self.name),
                ('state', 'in', ['sale', 'cancel']),
            ],
            'context': dict(self.env.context, default_booking_reference=self.name),
        }

    @api.depends('room_line_ids.checkin_date', 'room_line_ids.checkout_date')
    def _compute_checkin_checkout_dates(self):
        for booking in self:
            checkins = booking.room_line_ids.filtered(lambda l: l.checkin_date).mapped('checkin_date')
            checkouts = booking.room_line_ids.filtered(lambda l: l.checkout_date).mapped('checkout_date')
            booking.room_checkin_date = min(checkins) if checkins else False
            booking.room_checkout_date = max(checkouts) if checkouts else False

    @api.onchange('partner_id')
    def _onchange_partner_id_set_country(self):
        if self.partner_id and self.partner_id.country_id:
            self.country_id = self.partner_id.country_id

    @api.model
    def create(self, vals):

        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('room.booking') or '/'
        record = super(RoomBooking, self).create(vals)

        if record.partner_id and record.country_id:
            record.partner_id.country_id = record.country_id.id
        return record

    def write(self, vals):
        res = super(RoomBooking, self).write(vals)
        for rec in self:
            if rec.partner_id and rec.country_id:
                rec.partner_id.country_id = rec.country_id.id
        return res

    @api.depends('partner_id')
    def _compute_user_id(self):
        """Computes the User id"""
        for order in self:
            order.user_id = \
                order.partner_id.address_get(['invoice'])[
                    'invoice'] if order.partner_id else False

    def _compute_invoice_count(self):
        """Compute the invoice count"""
        for record in self:
            record.invoice_count = self.env['account.move'].search_count(
                [('ref', '=', self.name)])

    @api.depends('partner_id')
    def _compute_pricelist_id(self):
        """Computes PriceList"""
        for order in self:
            if not order.partner_id:
                order.pricelist_id = False
                continue
            order = order.with_company(order.company_id)
            order.pricelist_id = order.partner_id.property_product_pricelist

    @api.depends('room_line_ids.price_subtotal', 'room_line_ids.price_tax',
                 'room_line_ids.price_total',
                 'food_order_line_ids.price_subtotal',
                 'food_order_line_ids.price_tax',
                 'food_order_line_ids.price_total',
                 'service_line_ids.price_subtotal',
                 'service_line_ids.price_tax', 'service_line_ids.price_total',
                 'vehicle_line_ids.price_subtotal',
                 'vehicle_line_ids.price_tax', 'vehicle_line_ids.price_total',
                 'event_line_ids.price_subtotal', 'event_line_ids.price_tax',
                 'event_line_ids.price_total',
                 )
    def _compute_amount_untaxed(self, flag=False):
        """Compute the total amounts of the Sale Order"""
        amount_untaxed_room = 0.0
        amount_untaxed_food = 0.0
        amount_untaxed_fleet = 0.0
        amount_untaxed_event = 0.0
        amount_untaxed_service = 0.0
        amount_taxed_room = 0.0
        amount_taxed_food = 0.0
        amount_taxed_fleet = 0.0
        amount_taxed_event = 0.0
        amount_taxed_service = 0.0
        amount_total_room = 0.0
        amount_total_food = 0.0
        amount_total_fleet = 0.0
        amount_total_event = 0.0
        amount_total_service = 0.0
        room_lines = self.room_line_ids
        food_lines = self.food_order_line_ids
        service_lines = self.service_line_ids
        fleet_lines = self.vehicle_line_ids
        event_lines = self.event_line_ids
        booking_list = []
        account_move_line = self.env['account.move.line'].search_read(
            domain=[('ref', '=', self.name),
                    ('display_type', '!=', 'payment_term')],
            fields=['name', 'quantity', 'price_unit', 'product_type'], )
        for rec in account_move_line:
            del rec['id']
        if room_lines:
            amount_untaxed_room += sum(room_lines.mapped('price_subtotal'))
            amount_taxed_room += sum(room_lines.mapped('price_tax'))
            amount_total_room += sum(room_lines.mapped('price_total'))
            for room in room_lines:
                booking_dict = {'name': room.room_id.name,
                                'quantity': room.uom_qty,
                                'discount': room.discount,
                                'tax_ids': room.tax_ids.ids,
                                'price_unit': room.price_unit,
                                'product_type': 'room'}
                if booking_dict not in account_move_line:
                    if not account_move_line:
                        booking_list.append(booking_dict)
                    else:
                        for rec in account_move_line:
                            if rec['product_type'] == 'room':
                                if booking_dict['name'] == rec['name'] and \
                                        booking_dict['price_unit'] == rec[
                                    'price_unit'] and booking_dict['quantity'] \
                                        != rec['quantity']:
                                    booking_list.append(
                                        {'name': room.room_id.name,
                                         "quantity": booking_dict[
                                                         'quantity'] - rec[
                                                         'quantity'],
                                         "price_unit": room.price_unit,
                                         "product_type": 'room'})
                                else:
                                    booking_list.append(booking_dict)
                    if flag:
                        room.booking_line_visible = True
        if food_lines:
            for food in food_lines:
                booking_list.append(self.create_list(food))
            amount_untaxed_food += sum(food_lines.mapped('price_subtotal'))
            amount_taxed_food += sum(food_lines.mapped('price_tax'))
            amount_total_food += sum(food_lines.mapped('price_total'))
        if service_lines:
            for service in service_lines:
                booking_list.append(self.create_list(service))
            amount_untaxed_service += sum(
                service_lines.mapped('price_subtotal'))
            amount_taxed_service += sum(service_lines.mapped('price_tax'))
            amount_total_service += sum(service_lines.mapped('price_total'))
        if fleet_lines:
            for fleet in fleet_lines:
                booking_list.append(self.create_list(fleet))
            amount_untaxed_fleet += sum(fleet_lines.mapped('price_subtotal'))
            amount_taxed_fleet += sum(fleet_lines.mapped('price_tax'))
            amount_total_fleet += sum(fleet_lines.mapped('price_total'))
        if event_lines:
            for event in event_lines:
                booking_list.append(self.create_list(event))
            amount_untaxed_event += sum(event_lines.mapped('price_subtotal'))
            amount_taxed_event += sum(event_lines.mapped('price_tax'))
            amount_total_event += sum(event_lines.mapped('price_total'))
        for rec in self:
            rec.amount_untaxed = amount_untaxed_food + amount_untaxed_room + \
                                 amount_untaxed_fleet + \
                                 amount_untaxed_event + amount_untaxed_service
            rec.amount_untaxed_food = amount_untaxed_food
            rec.amount_untaxed_room = amount_untaxed_room
            rec.amount_untaxed_fleet = amount_untaxed_fleet
            rec.amount_untaxed_event = amount_untaxed_event
            rec.amount_untaxed_service = amount_untaxed_service
            rec.amount_tax = (amount_taxed_food + amount_taxed_room
                              + amount_taxed_fleet
                              + amount_taxed_event + amount_taxed_service)
            rec.amount_taxed_food = amount_taxed_food
            rec.amount_taxed_room = amount_taxed_room
            rec.amount_taxed_fleet = amount_taxed_fleet
            rec.amount_taxed_event = amount_taxed_event
            rec.amount_taxed_service = amount_taxed_service
            rec.amount_total = (amount_total_food + amount_total_room
                                + amount_total_fleet + amount_total_event
                                + amount_total_service)
            rec.amount_total_food = amount_total_food
            rec.amount_total_room = amount_total_room
            rec.amount_total_fleet = amount_total_fleet
            rec.amount_total_event = amount_total_event
            rec.amount_total_service = amount_total_service
        return booking_list



    @api.onchange('need_food')
    def _onchange_need_food(self):
        """Unlink Food Booking Line if Need Food is false"""
        if not self.need_food and self.food_order_line_ids:
            for food in self.food_order_line_ids:
                food.unlink()

    @api.onchange('need_service')
    def _onchange_need_service(self):
        """Unlink Service Booking Line if Need Service is False"""
        if not self.need_service and self.service_line_ids:
            for serv in self.service_line_ids:
                serv.unlink()

    @api.onchange('need_fleet')
    def _onchange_need_fleet(self):
        """Unlink Fleet Booking Line if Need Fleet is False"""
        if not self.need_fleet:
            if self.vehicle_line_ids:
                for fleet in self.vehicle_line_ids:
                    fleet.unlink()

    @api.onchange('need_event')
    def _onchange_need_event(self):
        """Unlink Event Booking Line if Need Event is False"""
        if not self.need_event:
            if self.event_line_ids:
                for event in self.event_line_ids:
                    event.unlink()

    @api.onchange('food_order_line_ids', 'room_line_ids',
                  'service_line_ids', 'vehicle_line_ids', 'event_line_ids')
    def _onchange_room_line_ids(self):
        """Invokes the Compute amounts function"""
        self._compute_amount_untaxed()
        self.invoice_button_visible = False

    @api.constrains("room_line_ids")
    def _check_duplicate_folio_room_line(self):
        """
        This method is used to validate the room_lines.
        ------------------------------------------------
        @param self: object pointer
        @return: raise warning depending on the validation
        """
        for record in self:
            # Create a set of unique ids
            ids = set()
            for line in record.room_line_ids:
                if line.room_id.id in ids:
                    raise ValidationError(
                        _(
                            """Room Entry Duplicates Found!, """
                            """You Cannot Book "%s" Room More Than Once!"""
                        )
                        % line.room_id.name
                    )
                ids.add(line.room_id.id)

    # def create_list(self, line_ids):
    #     """Returns a List of Dictionaries for Booking Lines"""
    #     booking_list = []
    #     for line in line_ids:
    #         model_name = line._name
    #         name = ""
    #         product_type = ""
    #         product_id = None
    #
    #         if model_name == 'room.booking.line':
    #             name = line.room_id.name
    #             product_id = line.room_id.id
    #             product_type = 'room'
    #         elif model_name == 'food.booking.line':
    #             name = line.food_id.name
    #             product_id = line.food_id.id
    #             product_type = 'food'
    #         elif model_name == 'fleet.booking.line':
    #             name = line.fleet_id.name
    #             product_id = line.fleet_id.id
    #             product_type = 'fleet'
    #         elif model_name == 'service.booking.line':
    #             name = line.service_id.name
    #             product_id = line.service_id.id
    #             product_type = 'service'
    #         elif model_name == 'event.booking.line':
    #             name = line.event_id.name
    #             product_id = line.event_id.id
    #             product_type = 'event'
    #         else:
    #             continue  # Unknown model
    #
    #         # Check for missing product
    #         if not product_id:
    #             raise ValidationError(_("Product is missing in one of the booking lines."))
    #
    #         booking_list.append({
    #             'name': name,
    #             'quantity': line.uom_qty,
    #             'price_unit': line.price_unit,
    #             'discount': getattr(line, 'discount', 0.0),
    #             'product_type': product_type,
    #             'product_id': product_id,
    #         })
    #
    #     return booking_list
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
                continue  # Unknown model, skip

            # Check for missing product
            if not product_id:
                raise ValidationError(_("Product is missing in one of the booking lines."))

            # Build the line dictionary
            line_data = {
                'name': name,
                'quantity': line.uom_qty,
                'price_unit': line.price_unit,
                'discount': getattr(line, 'discount', 0.0),
                'product_type': product_type,
                'product_id': product_id,
            }

            if model_name == 'food.booking.line':
                line_data['product_uom'] = line.uom_id.id
                line_data['line_type'] = 'food'

            booking_list.append(line_data)

        return booking_list
    def action_reserve(self):
        """Button Reserve Function"""
        if self.state == 'reserved':
            message = _("Room Already Reserved.")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': message,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        if self.room_line_ids:
            for room in self.room_line_ids:
                room.room_id.write({
                    'status': 'reserved',
                })
                room.room_id.is_room_avail = False
            self.write({"state": "reserved"})
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': "Rooms reserved Successfully!",
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        raise ValidationError(_("Please Enter Room Details"))

    def action_cancel(self):
        """
        @param self: object pointer
        """
        if self.room_line_ids:
            for room in self.room_line_ids:
                room.room_id.write({
                    'status': 'available',
                })
                room.room_id.is_room_avail = True
        self.write({"state": "cancel"})


    def action_maintenance_request(self):
        """
        Function that handles the maintenance request
        """
        room_list = []
        for rec in self.room_line_ids.room_id.ids:
            room_list.append(rec)
        if room_list:
            room_id = self.env['hotel.room'].search([
                ('id', 'in', room_list)])
            self.env['maintenance.request'].sudo().create({
                'date': fields.Date.today(),
                'state': 'draft',
                'type': 'room',
                'room_maintenance_ids': room_id.ids,
            })
            self.maintenance_request_sent = True
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': "Maintenance Request Sent Successfully",
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        raise ValidationError(_("Please Enter Room Details"))

    def action_done(self):

        for rec in self:
            if rec.quotation_state != 'sale':
                raise ValidationError(_('Your Payment is Due, please solve it first.'))

        _logger.info(f'=======aaaaaaaaaaalllllllllllllllllllll============{self.name}==================')
        self.write({"state": "done", "is_checkin": False})

        if self.room_line_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': "Booking Checked Out Successfully!",
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }

    def action_checkout(self):
        """Button action_heck_out function"""
        self.write({"state": "check_out"})
        for room in self.room_line_ids:
            room.room_id.write({
                'status': 'available',
                'is_room_avail': True
            })
            room.write({'checkout_date': datetime.today()})

    def action_invoice(self):
        """Method for creating invoice"""
        if not self.room_line_ids:
            raise ValidationError(_("Please Enter Room Details"))
        booking_list = self._compute_amount_untaxed(True)
        if booking_list:
            account_move = self.env["account.move"].create([{
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'partner_id': self.partner_id.id,
                'ref': self.name,
            }])
            for rec in booking_list:
                account_move.invoice_line_ids.create([{
                    'name': rec['name'],
                    'quantity': rec['quantity'],
                    'price_unit': rec['price_unit'],
                    'move_id': account_move.id,
                    'discount': rec.get('discount', 0.0),  # discount percentage
                    'tax_ids': [(6, 0, rec.get('tax_ids', []))],
                    'price_subtotal': rec['quantity'] * rec['price_unit'],
                    'product_type': rec['product_type'],
                }])
            self.write({'invoice_status': "invoiced"})
            self.invoice_button_visible = True
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoices',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'account.move',
                'view_id': self.env.ref('account.view_move_form').id,
                'res_id': account_move.id,
                'context': "{'create': False}"
            }

    def action_create_quotation(self):
        """Create a Sales Quotation (Sale Order) from room booking"""
        if not self.room_line_ids:
            raise ValidationError(_("Please Enter Room Details"))
        # Combine all booking lines
        all_lines = list(self.room_line_ids) + list(self.food_order_line_ids) + list(self.service_line_ids)
        # Generate booking list
        booking_list = self.create_list(all_lines)
        if booking_list:
            sale_order = self.env['sale.order'].create({
                'partner_id': self.partner_id.id,
                'booking_reference': self.name,
                'date_order': fields.Datetime.now(),
                'origin': self.name,
            })

            for rec in booking_list:
                self.env['sale.order.line'].create({
                    'order_id': sale_order.id,
                    'name': rec['name'],
                    'product_uom_qty': rec['quantity'],
                    'price_unit': rec['price_unit'],
                    'discount': rec.get('discount', 0.0),
                    'product_id': rec['product_id'],
                })

            self.write({'sale_order_id': sale_order.id})

            return {
                'type': 'ir.actions.act_window',
                'name': 'Quotation',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': sale_order.id,
            }

    def action_view_invoices(self):
        """Method for Returning invoice View"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'view_mode': 'list,form',
            'view_type': 'list,form',
            'res_model': 'account.move',
            'domain': [('ref', '=', self.name)],
            'context': "{'create': False}"
        }

    def action_checkin(self):
        """
        Check in the booking by validating room and ID details,
        updating room status, and changing the booking state.
        """
        today = date.today()

        for record in self:
            for line in record.room_line_ids:
                if line.checkin_date and line.checkin_date.date() != today:
                    raise ValidationError("Check-in date for all rooms must be today.")

        if not self.room_line_ids:
            raise ValidationError(_("Please Enter Room Details"))

        for room in record.room_line_ids:
            if room.room_id.status == 'occupied':
                raise ValidationError("Room is already occupied. Please ensure availability before check-in.")

        if not self.card_name_line_ids:
            raise UserError(_('Please add Your ID Details Before Checkin.'))

        for room in self.room_line_ids:
            room.room_id.write({'status': 'occupied'})
            room.room_id.is_room_avail = False
            room.write({'checkin_date': datetime.today()})

        self.write({"state": "check_in"})



        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Success'),
                'message': _('Booking Checked In Successfully!'),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def unlink(self):
        for room in self.room_line_ids:
            room.room_id.write({
                    'status': 'available',
                    'is_room_avail': True
                })

            if not self.env.user.has_group('base.group_no_one'):
                raise UserError("You are not allowed to delete Room.")

        return super(RoomBooking, self).unlink()

    def get_details(self):
        """ Returns different counts for displaying in dashboard"""
        today = datetime.today()
        tz_name = self.env.user.tz
        today_utc = pytz.timezone('UTC').localize(today,
                                                  is_dst=False)
        context_today = today_utc.astimezone(pytz.timezone(tz_name))
        total_room = self.env['product.template'].search_count([('is_roomtype', '=', True)])
        # check_in = self.env['room.booking.line'].search_count(
        #     [('state', '=', 'check_in')])

        check_in = self.env['product.template'].search_count(
            [('status', '=', 'occupied'), ('is_roomtype', '=', True)],)

        available_room = self.env['product.template'].search(
            [('status', '=', 'available'), ('is_roomtype', '=', True)],)
        domain = [
            ('state', '=', 'reserved'),
            ('checkin_date', '>=', context_today.date()),
            ('checkin_date', '<=', context_today.date())
        ]
        reservation = self.env['room.booking.line'].search(domain)

        # reservation = self.env['product.template'].search(
        #     [('status', '=', 'reserved'), ('is_roomtype', '=', True)], )

        reserved_lines = self.env['room.booking.line'].search([
            ('state', '=', 'reserved'),
            ('checkin_date', '<=', context_today.date()),
            ('checkout_date', '>', context_today.date()),  # Optional if you have it
        ])
        booked_room_ids = reserved_lines.mapped('room_id.id')

        # Step 2: Get rooms currently occupied
        check_in_rooms = self.env['product.template'].search([
            ('status', '=', 'occupied'),
            ('is_roomtype', '=', True)
        ])

        # Step 3: Available today = not reserved today and not occupied
        today_available = self.env['product.template'].search([
            ('is_roomtype', '=', True),
            ('id', 'not in', booked_room_ids),
            ('id', 'not in', check_in_rooms.ids),
        ])

        # combined_rooms = available_room + future_reserved
        check_outs = self.env['room.booking.line'].search([('state', '=', 'check_out'),('checkout_date', '>=', context_today.date()),
            ('checkout_date', '<=', context_today.date())])
        check_out = 0
        staff = 0
        # for rec in check_outs:
        #     for room in rec.room_line_ids:
        #         if room.checkout_date.date() == context_today.date():
        #             check_out += 1
        """staff"""
        staff = self.env['res.users'].search_count(
            [('groups_id', 'in',
              [self.env.ref('hotel_management_odoo.hotel_group_admin').id,
               self.env.ref(
                   'hotel_management_odoo.cleaning_team_group_head').id,
               self.env.ref(
                   'hotel_management_odoo.cleaning_team_group_user').id,
               self.env.ref(
                   'hotel_management_odoo.hotel_group_reception').id,
               self.env.ref(
                   'hotel_management_odoo.maintenance_team_group_leader').id,
               self.env.ref(
                   'hotel_management_odoo.maintenance_team_group_user').id
               ])])
        total_vehicle = self.env['fleet.vehicle.model'].search_count([])
        available_vehicle = total_vehicle - self.env[
            'fleet.booking.line'].search_count(
            [('state', '=', 'check_in')])
        total_event = self.env['event.event'].search_count([])
        pending_event = self.env['event.event'].search([])
        pending_events = 0
        today_events = 0
        for pending in pending_event:
            if pending.date_end and pending.date_end >= datetime.now():
                pending_events += 1
            if pending.date_end and pending.date_end.date() == date.today():
                today_events += 1
        food_items = self.env['product.template'].search_count([('is_foodtype', '=', True)])
        food_order = len(self.env['food.booking.line'].search([]).filtered(
            lambda r: r.booking_id.state not in ['check_out', 'cancel',
                                                 'done']))
        """total Revenue"""
        total_revenue = 0
        today_revenue = 0
        pending_payment = 0
        month_revenue = 0
        year_revenue = 0
        today = fields.Date.today()
        current_month = today.month
        current_year = today.year
        fiscal_year = self.env['account.fiscal.year'].search([
            ('date_from', '<=', today),
            ('date_to', '>', today)
        ], limit=1)
        for rec in self.env['account.move'].search(
                [('payment_state', '=', 'paid')]):
            if rec.booking_reference:

                total_revenue += rec.amount_total
                if rec.date == fields.Date.today():
                    today_revenue += rec.amount_total

                if rec.date.month == current_month and rec.date.year == current_year:
                    month_revenue += rec.amount_total

                if fiscal_year and fiscal_year.date_from <= rec.date < fiscal_year.date_to:
                    year_revenue += rec.amount_total
        _logger.info(f'=======dddddd======{year_revenue}==============================')

        for rec in self.env['account.move'].search(
                [('payment_state', '=', 'not_paid')]):
            if rec.booking_reference:
                pending_payment += rec.amount_total
        return {
            'total_room': total_room,
            'context_today': str(context_today),
            'available_room': len(today_available),
            'staff': staff,
            'check_in': check_in,
            'reservation':len(reservation),
            'check_out': len(check_outs),
            'total_vehicle': total_vehicle,
            'available_vehicle': available_vehicle,
            'total_event': total_event,
            'today_events': today_events,
            'pending_events': pending_events,
            'food_items': food_items,
            'food_order': food_order,
            'total_revenue': round(total_revenue, 2),
            'today_revenue': round(today_revenue, 2),
            'month_revenue': round(month_revenue, 2),
            'year_revenue': round(year_revenue, 2),
            'pending_payment': round(pending_payment, 2),
            'currency_symbol': self.env.user.company_id.currency_id.symbol,
            'currency_position': self.env.user.company_id.currency_id.position
        }
