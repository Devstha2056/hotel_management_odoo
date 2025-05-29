
from odoo import fields, models

class MaintenanceTeam(models.Model):
    """Model that handles the maintenance team """
    _name = "maintenance.team"
    _description = "Maintenance Team"

    name = fields.Char(string='Maintenance Team',
                       help='Name of the maintenance team')
    user_id = fields.Many2one('res.users', string='Team Leader',
                              help="Leader of Team",
                              domain=lambda self: [
                                  ('groups_id', 'in', self.env.ref(
                                      'hotel_management_odoo.'
                                      'maintenance_team_group_'
                                      'leader').id)])
    member_ids = fields.Many2many('res.users', string='Members',
                                  help="Members of the Team",
                                  domain=lambda self: [
                                      ('groups_id', 'in', self.env.ref(
                                          'hotel_management_odoo.'
                                          'maintenance_'
                                          'team_group_user').id)])
