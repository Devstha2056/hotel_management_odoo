from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError,UserError

class IDMaster(models.Model):
    _name = 'id.master'
    _description = 'Master List of ID Document Types'
    _rec_name='name'

    name = fields.Char('Document Type', required=True, translate=True)

    active = fields.Boolean(string='Active', default=True)

    def unlink(self):
        if not self.env.user.has_group('base.group_no_one'):
            raise UserError("You are not allowed to delete Restaurant Orders.")
        return super(IDMaster, self).unlink()





