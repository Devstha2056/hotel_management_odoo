import io
import json
from odoo.tools.safe_eval import pytz
from odoo import fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import json_default
from datetime import datetime, timedelta, date
import logging

_logger = logging.getLogger(__name__)

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

class RoomBookingWizard(models.TransientModel):
    """PDF Report for Room Booking"""

    _name = "room.booking.detail"
    _description = "Room Booking Details"

    report_date = fields.Date(string="Report Date", required=True, default=fields.Date.context_today)

    def action_room_booking_pdf(self):
        """Generate and trigger Room Booking PDF report"""
        data = {
            "booking": self.generate_data(),
        }
        return self.env.ref(
            "hotel_management_odoo.action_report_room_booking"
        ).report_action(self, data=data)


    def action_show_booking_lines(self):
        """Prepare data and open tree view"""
        # Clear old records for this wizard (optional)
        self.env['room.booking.line.temp'].search([('wizard_id', '=', self.id)]).unlink()

        data = self.generate_data()

        for line in data:
            self.env['room.booking.line.temp'].create({
                'room_name': line['room_name'],
                'status': line['status'],
                'partner_id': line['partner_id'],
                'checkin_date': line['checkin_date'],
                'checkout_date': line['checkout_date'],
                'wizard_id': self.id,
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Room Booking Details',
            'res_model': 'room.booking.line.temp',
            'view_mode': 'list',
            'target': 'current',
            'domain': [('wizard_id', '=', self.id)],
        }

    def generate_data(self):
        result = []

        selected_date = self.report_date

        all_rooms = self.env['product.template'].search([('is_roomtype', '=', True)])

        for room in all_rooms:
            room_data = {
                'room_name': room.name,
                'status': room.status,
                'partner_id': '',
                'checkin_date': False,  # use False instead of ''
                'checkout_date': False,  # use False instead of ''
            }

            if room.status in ['reserved', 'occupied']:
                booking_line = self.env['room.booking.line'].search([
                    ('room_id.product_tmpl_id', '=', room.id),
                    ('checkin_date', '<=', selected_date),
                ], limit=1)

                if booking_line:
                    room_data['partner_id'] = booking_line.booking_id.partner_id.name or ''
                    room_data['checkin_date'] = booking_line.checkin_date or False
                    room_data['checkout_date'] = booking_line.checkout_date or False

            result.append(room_data)

        return result

    def action_room_booking_excel(self):
        """Button action for creating Room Booking Excel report"""
        data = {
            "booking": self.generate_data(),
        }
        return {
            "type": "ir.actions.report",
            "data": {
                "model": "room.booking.detail",
                "options": json.dumps(data, default=json_default),
                "output_format": "xlsx",
                "report_name": "Excel Report",
            },
            "report_type": "xlsx",
        }


    def get_xlsx_report(self, data, response):
        """Organizing xlsx report"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format(
            {"font_size": "14px", "bold": True, "align": "center",
             "border": True}
        )
        head = workbook.add_format(
            {"align": "center", "bold": True, "font_size": "23px",
             "border": True}
        )
        body = workbook.add_format(
            {"align": "left", "text_wrap": True, "border": True})
        sheet.merge_range("A1:F1", "Room Booking", head)
        sheet.set_column("A2:F2", 18)
        sheet.set_row(0, 30)
        sheet.set_row(1, 20)
        sheet.write("A2", "Sl No.", cell_format)
        sheet.write("B2", "Guest Name", cell_format)
        sheet.write("C2", "Room No.", cell_format)
        sheet.write("D2", "Check In", cell_format)
        sheet.write("E2", "Check Out", cell_format)
        sheet.write("F2", "Reference No.", cell_format)
        row = 2
        column = 0
        value = 1
        for i in data["booking"]:
            sheet.write(row, column, value, body)
            sheet.write(row, column + 1, i["partner_id"], body)
            sheet.write(row, column + 2, i["room"], body)
            sheet.write(row, column + 3, i["checkin_date"], body)
            sheet.write(row, column + 4, i["checkout_date"], body)
            sheet.write(row, column + 5, i["name"], body)
            row = row + 1
            value = value + 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
