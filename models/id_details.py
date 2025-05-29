from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

class IDMaster(models.Model):
    _name = 'id.master'
    _description = 'Master List of ID Document Types'
    _rec_name='name'

    name = fields.Char('Document Type', required=True, translate=True)





