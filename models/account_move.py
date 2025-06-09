
from odoo import fields, models,api

import odoo.addons.decimal_precision as dp
class AccountMove(models.Model):
    _inherit = "account.move"

    hotel_booking_id = fields.Many2one(
        'room.booking',
        string="Booking Reference",
        help="Choose the Booking Reference"
    )
    booking_reference = fields.Char(string='Booking Reference', readonly=True)


    @api.depends('invoice_line_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for invoice in self:
            amount_untaxed = amount_tax = amount_discount = amount_subtotal = 0.0
            for line in invoice.invoice_line_ids:

                amount_untaxed += line.price_subtotal
                amount_tax += (line.price_total - line.price_subtotal)
                amount_discount += (line.quantity * line.price_unit * line.discount) / 100
                amount_subtotal += (line.price_subtotal + amount_discount)
            invoice.update({
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