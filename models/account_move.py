from odoo import fields, models,api
import odoo.addons.decimal_precision as dp

from num2words import num2words



class AccountMove(models.Model):
    _inherit = "account.move"

    hotel_booking_id = fields.Many2one(
        'room.booking',
        string="Booking Reference",
        help="Choose the Booking Reference"
    )
    booking_reference = fields.Char(string='Booking Reference', readonly=True)

    @api.model
    def amount_to_text(self, amount, currency):
        # Handle zero amount explicitly
        if amount == 0:
            return "ZERO ONLY".upper()

        # Split the amount into integer and decimal parts
        integer_part = int(amount)
        decimal_part = round((amount - integer_part) * 100)  # Converts decimal part to integer percentage

        # Convert integer and decimal parts to words
        integer_in_words = num2words(integer_part, lang='en')
        decimal_in_words = num2words(decimal_part, lang='en')

        # Handle NPR currency
        if currency.upper() == 'NPR':
            currency_in_words = 'Rupee' if integer_part == 1 else 'Rupees'
            result = f"{integer_in_words} {currency_in_words} and {decimal_in_words} Paisa only"
        else:
            # Handle other currencies
            result = f"{integer_in_words} {currency} and {decimal_in_words} {currency} only"

        return result.upper()


    #
    # @api.depends('invoice_line_ids.price_total')
    # def _amount_all(self):
    #     """
    #     Compute the total amounts of the SO.
    #     """
    #     for invoice in self:
    #         amount_untaxed = amount_tax = amount_discount = amount_subtotal = 0.0
    #         for line in invoice.invoice_line_ids:
    #
    #             amount_untaxed += line.price_subtotal
    #             amount_tax += (line.price_total - line.price_subtotal)
    #             amount_discount += (line.quantity * line.price_unit * line.discount) / 100
    #             amount_subtotal += (line.price_subtotal + amount_discount)
    #         invoice.update({
    #             'amount_untaxed': amount_untaxed,
    #             'amount_tax': amount_tax,
    #             'amount_discount': amount_discount,
    #             'amount_subtotal':amount_subtotal,
    #             'amount_total': amount_untaxed + amount_tax,
    #         })
    #
    #
    # amount_untaxed = fields.Monetary(string='Taxable Amount', store=True, readonly=True, compute='_amount_all',
    #                                  track_visibility='always')
    #
    # amount_subtotal = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
    #                                  track_visibility='always')
    #
    #
    # amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all',
    #                              track_visibility='always')
    #
    # amount_total = fields.Monetary(string=' Grand Total', store=True, readonly=True, compute='_amount_all',
    #                                track_visibility='always')
    # amount_discount = fields.Monetary(string='Discount Amount', store=True, readonly=True, compute='_amount_all',
    #                                   digits=dp.get_precision('Account'), track_visibility='always')