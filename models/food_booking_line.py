
from odoo import api, fields, models, tools


class FoodBookingLine(models.Model):
    """Model that handles the food booking"""
    _name = "food.booking.line"
    _description = "Hotel Food Line"
    _rec_name = 'food_id'

    @tools.ormcache()
    def _get_default_uom_id(self):
        """Method for getting the default uom id"""
        return self.env.ref('uom.product_uom_unit')

    booking_id = fields.Many2one("room.booking", string="Booking",
                                 help="Shows the room Booking",
                                 ondelete="cascade")

    booking_ids = fields.Many2one("restaurant.order", string="Booking",
                                 help="Shows the room Booking",
                                 ondelete="cascade",domain="[('state','=','confirm')]")

    kot_order_id = fields.Many2one(
        'hotel.restaurant.kitchen.order.tickets',
        string='KOT Order',
        help='Kitchen Order this food booking line is part of'
    )

    bot_order_id = fields.Many2one(
        'hotel.restaurant.bar.order.tickets',
        string='BOT Order',
        help='Bar Order this food booking line is part of'
    )

    restaurant_order_id = fields.Many2one(
        'restaurant.order',
        string='Restaurant Order',
        help='Restaurant Order this food booking line is part of'
    )

    product_nature = fields.Selection(
        related='food_id.product_tmpl_id.product_nature',
        string='Product Nature',
        store=True,
        readonly=True,
    )

    room_booking_id = fields.Many2one(related='booking_ids.folio_ids', string='Room Booking', store=True)


    food_id = fields.Many2one('product.product', string="Product",
                              help="Indicates the Food Product")
    description = fields.Char(string='Description',
                              help="Description of Food Product",
                              related='food_id.display_name')
    uom_qty = fields.Float(string="Qty", default=1,
                           help="The quantity converted into the UoM used by "
                                "the product")
    uom_id = fields.Many2one('uom.uom', readonly=True,
                             string="Unit of Measure",
                             default=_get_default_uom_id, help="This will set "
                                                               "the unit of"
                                                               " measure used")
    price_unit = fields.Float(string='Rent',
                              digits='Product Price',
                              help="The rent price of the selected room.")

    tax_ids = fields.Many2many('account.tax',
                               'hotel_room_order_line_taxes_rel',
                               'food_id', 'tax_id',
                               related='food_id.taxes_id',
                               string='Taxes',
                               help="Default taxes used when selling the room."
                               , domain=[('type_tax_use', '=', 'sale')])

    currency_id = fields.Many2one(string='Currency',
                                  related='booking_id.pricelist_id.currency_id'
                                  , help='The currency used')
    price_subtotal = fields.Float(string="Subtotal",
                                  compute='_compute_price_subtotal',
                                  help="Total Price excluding Tax",
                                  store=True)

    price_tax = fields.Float(string="Total Tax",
                             compute='_compute_price_subtotal',
                             help="Tax Amount",
                             store=True)
    price_total = fields.Float(string="Total",
                               compute='_compute_price_subtotal',
                               help="Total Price including Tax",
                               store=True)
    state = fields.Selection(related='booking_id.state',
                             string="Order Status",
                             help=" Status of the Order",
                             copy=False)
    booking_line_visible = fields.Boolean(default=False,
                                          string="Booking Line Visible",
                                          help="If True, then Booking Line "
                                               "will be visible")

    discount = fields.Float(string="Discount (%)", default=0.0)

    @api.onchange("food_id")
    def _get_list_price(self):
        for line in self:
            if line.food_id:
                line.price_unit = line.food_id.list_price
                line.tax_ids = line.food_id.taxes_id

    @api.depends('uom_qty', 'price_unit', 'tax_ids')
    def _compute_price_subtotal(self):
        """Compute the amounts of the room booking line."""
        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()
            self.env['account.tax']._add_tax_details_in_base_line(base_line, self.env.company)
            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            print("total_excluded_currency", line.price_subtotal)
            line.price_total = base_line['tax_details']['raw_total_included_currency']
            print("total_included_currency", line.price_total)
            line.price_tax = line.price_total - line.price_subtotal
            if self.env.context.get('import_file',
                                    False) and not self.env.user. \
                    user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_recordset(
                    ['invoice_repartition_line_ids'])



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
                'partner_id': self.booking_id.partner_id,
                'currency_id': self.currency_id,
            },
        )

    def search_food_orders(self):
        """Returns list of food orders"""
        return (self.search([]).filtered(lambda r: r.booking_id.state not in [
            'check_out', 'cancel', 'done']).ids)



# @api.depends('uom_qty', 'price_unit', 'tax_ids', )
    # def _compute_price_subtotal(self):
    #     """Compute the amounts of the room booking line with discount."""
    #     for line in self:
    #         base_line = line.env['account.tax']._prepare_base_line_for_taxes_computation(
    #             line,
    #             **{
    #                 'price_unit': line.price_unit,
    #                 'quantity': line.uom_qty,
    #                 'currency_id': line.currency_id,
    #                 'partner': line.booking_id.partner_id,
    #                 'tax_ids': line.tax_ids,
    #             }
    #         )
    #
    #         line.env['account.tax']._add_tax_details_in_base_line(base_line, line.env.company)
    #
    #         line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
    #         line.price_total = base_line['tax_details']['raw_total_included_currency']
    #         line.price_tax = line.price_total - line.price_subtotal