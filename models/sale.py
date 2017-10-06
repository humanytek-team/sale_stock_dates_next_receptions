# -*- coding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2017 Humanytek (<www.humanytek.com>).
#    Manuel Márquez <manuel@humanytek.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from datetime import datetime
from pytz import timezone

from openerp import api, models
from openerp.tools.translate import _


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def _get_date_to_user_timezone(self, datetime_to_convert):
        """Returns the datetime received converted to a date set to
        timezone of user"""

        tz = self.env.context.get('tz', False)
        if not tz:
            tz = 'America/Mexico_City'

        datetime_now_with_tz = datetime.now(timezone(tz))
        utc_difference_timedelta = datetime_now_with_tz.utcoffset()
        datetime_to_convert = datetime.strptime(
            datetime_to_convert, '%Y-%m-%d %H:%M:%S')
        datetime_result = datetime_to_convert + utc_difference_timedelta
        date_result = datetime_result.strftime('%d-%m-%Y')

        return date_result

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):

        if self.product_id.type == 'product':
            product_qty = self.env['product.uom']._compute_qty_obj(
                self.product_uom,
                self.product_uom_qty,
                self.product_id.uom_id)

            if product_qty > (self.product_id.qty_available -
                self.product_id.outgoing_qty):

                if self.product_id.incoming_qty > 0:

                    StockPicking = self.env['stock.picking']

                    tz = self.env.context.get('tz', False)
                    if not tz:
                        tz = 'America/Mexico_City'

                    datetime_now_with_tz = datetime.now(timezone(tz))
                    datetime_now = datetime_now_with_tz.strftime(
                        '%Y-%m-%d %H:%M:%S'
                    )

                    pickings = StockPicking.search([
                        ('picking_type_id.code', '=', 'incoming'),
                        ('state', '=', 'assigned'),
                        ('move_lines_related.product_id', '=',
                         self.product_id.id),
                        ('min_date', '>=', datetime_now),
                    ], order='min_date')

                    if pickings:

                        date_next_receipt = self._get_date_to_user_timezone(
                            pickings[0].min_date)

                        warning_mess = {
                            'title': _('Not enough inventory!'),
                            'message' : _('You plan to sell %.2f %s but the stock on hand is %.2f %s. The date of the next receipt is %s') % \
                                (
                                    self.product_uom_qty,
                                    self.product_uom.name,
                                    self.product_id.qty_available,
                                    self.product_id.uom_id.name,
                                    date_next_receipt
                                )}

                        return {'warning': warning_mess}

        onchange_response = super(
            SaleOrderLine, self)._onchange_product_id_check_availability()

        if onchange_response:
            return onchange_response
