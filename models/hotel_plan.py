from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

class HotelPlan(models.Model):
    """Model that holds all details regarding hotel plan"""
    _name = 'hotel.plan'
    _description = 'Hotel plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name='meal_plan_id'

    occupancy = fields.Selection(selection=[("1", "Single"),
                                            ("2", "Double"),
                                            ("3", "Triple")],
                                 required=True, tracking=True,
                                 string="Occupancy",
                                 help="Occupancy of The Room", )

    meal_plan_id = fields.Many2one('meal.plan', string='Meal Plan', ondelate='cascade')

    price = fields.Float(string='Base Price')

    cat_id = fields.Many2one('product.category', string="Category", required=True, ondelete="cascade")
    active = fields.Boolean(string='Active', default=True)
    def unlink(self):
        if not self.env.user.has_group('base.group_no_one'):
            raise UserError("You are not allowed to delete Restaurant Orders.")
        return super(HotelPlan, self).unlink()


class MealPlan(models.Model):
    """Model that holds all details regarding hotel plan"""
    _name = 'meal.plan'
    _description = 'Meal plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'meal_plan'

    meal_plan = fields.Char(string='Meal Plan', required=True)

    active = fields.Boolean(string='Active', default=True)

    def unlink(self):
        if not self.env.user.has_group('base.group_no_one'):
            raise UserError("You are not allowed to delete Restaurant Orders.")
        return super(MealPlan, self).unlink()
