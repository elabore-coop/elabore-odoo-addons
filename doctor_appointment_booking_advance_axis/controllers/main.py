# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
import uuid
from babel.dates import format_datetime, format_date
from datetime import date, datetime
from werkzeug.urls import url_encode

from odoo import http, _, fields
from odoo.http import request
from odoo.tools import html2plaintext, DEFAULT_SERVER_DATETIME_FORMAT as dtf
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools.misc import get_lang


class WebsiteCalendar(http.Controller): 
    
    @http.route([
        '/appointment/select',
    ], type='http', auth="public", website=True)
    def appointment_country_choice(self, message=None, **kwargs):
        appoint_with_state = request.env['appointment.group'].sudo().search([('state_id', '!=', False)])
        appoint_without_state = request.env['appointment.group'].sudo().search([('state_id', '=', False)])

        appoint_groups_ids = []
        state_list = []
        for rec in appoint_with_state:
            if rec.state_id.id not in state_list:
                appoint_groups_ids.append(rec.id)
                state_list.append(rec.state_id.id)

        country_list = []
        for rec in appoint_without_state:
            if rec.country_id.id not in country_list:
                appoint_groups_ids.append(rec.id)
                country_list.append(rec.country_id.id)

        appoint_group = request.env['appointment.group'].sudo().search([('id', 'in', appoint_groups_ids)])
        value = {'appoint_group': appoint_group}
        return request.render("doctor_appointment_booking_advance_axis.appointment_country", value)

    @http.route([
        '/appointment/',
        '/appointment/<int:state_id>',
    ], type='http', auth="public", website=True)
    def appointment_group_choice(self,state_id=None,  appointment_type=None,
                                 employee_id=None, message=None, **post):
        domain = [('country_id', '=', int(post.get('country_id')))]
        if state_id:
            domain += [('state_id', '=', state_id)]
        appoint_group = request.env['appointment.group'].sudo().search(domain)
        appoint_group_id = request.env['appointment.group'].sudo().search([('id', '=', post.get('group_id'))])
        value={
            'appoint_group':appoint_group,
            'appoint_group_id': appoint_group_id.id,
        }
        return request.render("doctor_appointment_booking_advance_axis.appointment_1", value)

    @http.route(['/website/appointment'], type='http', method=["POST"], auth="public", website=True)
    def appointees_info(self, prev_emp=False, **post):
        country_id = post.get('country_id')
        if 'id' in post:
            appoint_group_ids = request.env['appointment.group'].sudo().search([('id','=', post.get('id'))])
        partner_ids = []
        # appointment_type = []
        for record in appoint_group_ids:
            for rec in record.appointment_group_ids:
                partner_ids.append(rec.id)
                # appointment_type.append(j.appointment_type.id)
        value={
            'appoint_group_ids':appoint_group_ids,
            'country':country_id,
            # 'appointment_type': appointment_type
        }
        return request.render("doctor_appointment_booking_advance_axis.appointees_availability",value)

    @http.route(['/website/appointment/slot'], type='http', auth="public", website=True)
    def appointment_slots(self,appointment_type=None,timezone=None, prev_emp=False, **post):
        appoint_group_id = request.env['appointment.group'].sudo().search([('id','=',post.get('product_id'))])
        country_id = post.get('country_id')
        appointment_timeslots = request.env['res.partner'].sudo().search([('id','=', post.get('id'))])
        appointment_type = request.env['calendar.appointment.type'].sudo().search([('partner_id.id','=',post.get('id'))])
        value = {}
        if appointment_type:
            request.session['timezone'] = timezone or appointment_type.appointment_tz
            Slots = appointment_type.sudo()._get_appointment_slots(request.session['timezone'], appointment_type)
            value.update({
                'appointment_type':appointment_type,
                'slots':Slots,
                'country_id':country_id,
                'appoint_group_id': appoint_group_id

            })
            return request.render("doctor_appointment_booking_advance_axis.slot", value)
        else:
            return request.render("doctor_appointment_booking_advance_axis.slot_available")

    @http.route(['/website/appointment/form/<model("calendar.appointment.type"):appointment_type>/info'], type='http', auth="public", website=True)
    def appointment_form(self,appointment_type, **post):
        appoint_group_id = request.env['appointment.group'].sudo().search([('id', '=', post.get('group_product_id'))])

        request.session['partner_get'] = appointment_type.partner_id.id
        country_id = post.get("country")
        partner_id = request.env['res.partner'].sudo().search([('id','=',request.env.user.partner_id.id)])
        partner_data = {}
        if request.env.user.partner_id != request.env.ref('base.public_partner'):
            partner_data = request.env.user.partner_id.read(fields=['name', 'mobile', 'country_id', 'email'])[0]
        date_time = post.get('date_time')
        day_name = format_datetime(datetime.strptime(date_time, dtf), 'EEE', locale=get_lang(request.env).code)
        date_formated = format_datetime(datetime.strptime(date_time, dtf), locale=get_lang(request.env).code)
        country_get = request.env['appointment.group'].sudo().search([])

        return request.render("doctor_appointment_booking_advance_axis.appointment_form", {
            'partner_data': partner_data,
            'appointment_type': appointment_type,
            'datetime': date_time,
            'datetime_locale': day_name + ' ' + date_formated,
            'datetime_str': date_time,
            'country': country_id,
            'partner_name':partner_id.name,
            'partner_email':partner_id.email,
            'partner_phone':partner_id.phone,
            'appoint_group_id': appoint_group_id
        })                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                

    @http.route(['/website/calendar/<model("calendar.appointment.type"):appointment_type>/submit'], type='http', auth="public", website=True, method=["POST"])
    def calendar_appointment_submit(self, appointment_type, country_id=False, **kwargs):
        appoint_group_id = request.env['appointment.group'].sudo().search([('id', '=', kwargs.get('appoint_group_id'))])
        name = kwargs.get('name') or ''
        phone = kwargs.get('phone') or ''
        last_name = kwargs.get('last_name') or ''
        description = kwargs.get('description') or ''
        email = kwargs.get('email') or ''
        datetime_str = kwargs.get('date_time')
        timezone = request.session['timezone']
        tz_session = pytz.timezone(timezone)
        date_start = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
        date_end = date_start + relativedelta(hours=appointment_type.appointment_duration)
        country_id = int(country_id) if country_id else None
        country_name = country_id and request.env['res.country'].browse(country_id).name or ''
        #Partner = request.env['res.partner'].sudo().search([('id','=', partner)])
        Partner = request.env['res.partner'].sudo().search([('email', '=like', email)], limit=1)

        if Partner:
            if not Partner.mobile or len(Partner.mobile) <= 5 and len(phone) > 5:
                Partner.write({'mobile': phone,
                               'last_name': last_name,
                               'comment': description})
            if not Partner.country_id:
                Partner.country_id = country_id
            Partner.start_datetime = date_start.strftime(dtf)
        else:
            Partner = request.env['res.partner'].sudo().create({
                'name': name,
                'country_id': country_id,
                'mobile': phone,
                'email': email,
                'start_datetime': date_start.strftime(dtf),
                'last_name': last_name,
                'comment': description
            })
        attendee = Partner.name + ' ' + Partner.last_name
        description = ('Attendee: %s\n'
                       'Country: %s\n'
                       'Mobile: %s\n'
                       'Email: %s\n'
                       'Note: %s\n' % (attendee, country_name, phone, email, description))

        for question in appointment_type.question_ids:
            key = 'question_' + str(question.id)
            if question.question_type == 'checkbox':
                answers = question.answer_ids.filtered(lambda x: (key + '_answer_' + str(x.id)) in kwargs)
                description += question.name + ': ' + ', '.join(answers.mapped('name')) + '\n'
            elif kwargs.get(key):
                if question.question_type == 'text':
                    description += '\n* ' + question.name + ' *\n' + kwargs.get(key, False) + '\n\n'
                else:
                    description += question.name + ': ' + kwargs.get(key) + '\n'

        categ_id = request.env.ref('doctor_appointment_booking_advance_axis.calendar_event_type_data_online_appointment')
        alarm_ids = appointment_type.reminder_ids and [(6, 0, appointment_type.reminder_ids.ids)] or []
        start_time = str(date_start.time())
        end_time = str(date_end.time())

        event = request.env['calendar.event'].sudo().create({
            'name': appointment_type.name,
            'start': date_start.strftime(dtf),
            'start_at':date_start.date(),
            'stop': date_end,
            'description': description,
            'partner_new': Partner.id,
            # 'partner_ids': Partner.id,
            'appointment_type_id': appointment_type.id,
            'start_time':start_time,
            'end_time':end_time,
            'doctore_id' : appointment_type.partner_id.id


        })
        calendar_attendee = request.env['calendar.attendee'].sudo().create(
            {'partner_id': Partner.id,
             'state': 'needsAction',
             'email': email,
             'event_id': event.id})

        event.write({'attendee_ids': [(6, 0, [i.id for i in calendar_attendee])]})
        request.session['event'] = event.id
        product_list = []
        product_dict = {}
        partner_get = request.session.get('partner_get')
        partner = request.env['res.partner'].sudo().search([('id','=', partner_get)])

        product = request.env['product.product'].sudo().search([('name','ilike',appoint_group_id.product_template_id.name)])
        order = request.env['sale.order'].sudo().create({
            'partner_id': Partner.id,
            'partner_shipping_id': appointment_type.partner_id.id,
            'order_line':[(0, 0, {
                    'product_id':product.id,
                    'price_unit':partner.appointment_charge,
                })],
        })
        acquirers = request.env['payment.acquirer'].sudo().search([('state','!=','disabled')])
        order_data = request.website.sale_get_order()
        if order:
            request.session['sale_order_id'] = order.id
        request.session['sale_last_order_id'] = order.id
        value = {
            'event': event,
            'start_time':start_time,
            'end_time':end_time,
            'website_sale_order':order,
            'acquirers':acquirers,
            'order_id':order.id,
            'access_token': str(uuid.uuid4()),
            'success_url': 'shop/payment/transaction',
            'error_url':'error',
            'callback_method':'callback_method',
            'order': order,
        }

        return request.render('doctor_appointment_booking_advance_axis.payment_option',value)

    @http.route('/appointment/confirmation', type='http', auth="public", website=True, sitemap=False)
    def payment_validate(self, **kwargs):
        sale_order_id = request.session.get('sale_last_order_id')
        order = request.env['sale.order'].sudo().search([('id','=', sale_order_id)])
        event_id = request.session.get('event')
        event = request.env['calendar.event'].sudo().browse(event_id)
        value = {
            'event':event,
            'order':order,
        }
        return request.render('doctor_appointment_booking_advance_axis.appointment_confirm',value)

class WebsiteSale(WebsiteSale):

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def payment_confirmation(self, **post):
        """ End of checkout process controller. Confirmation is basically seing
        the status of a sale.order. State at this point :

         - should not have any context / session info: clean them
         - take a sale.order id, because we request a sale.order and are not
           session dependant anymore
        """
        sale_order_id = request.session.get('sale_last_order_id')
        event_id = request.session.get('event')
        if (sale_order_id and event_id):
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            return request.redirect('/appointment/confirmation')
        else:
            if (sale_order_id and not event_id):
                order = request.env['sale.order'].sudo().browse(sale_order_id)
                return request.render("website_sale.confirmation", {'order': order})
            else:
                return request.redirect('/shop')


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        user = request.env.user
        is_admin = request.env['res.users'].browse(user.id)._is_admin()
        if is_admin:
            calender_list = request.env['calendar.event'].search([])
            calender_ids= [i.id for i in calender_list if i.doctore_id]
            values['appointment_count'] = request.env['calendar.event'].search_count([('id', 'in', calender_ids)])
        else:
            values['appointment_count'] = request.env['calendar.event'].sudo().search_count([('doctore_id','=',user.partner_id.id)])        
        if values.get('sales_user', False):
            values['title'] = _("Salesperson")
        return values

    def _ticket_get_page_view_values(self, appointments, access_token, **kwargs):
        values = {
            'page_name': 'appointments',
            'appointments': appointments,
        }
        return self._get_page_view_values(appointments, access_token, values, False, **kwargs)

    @http.route(['/my/appointments'], type='http', auth="user", website=True)
    def my_appointments(self, page=1, date_begin=None, date_end=None, sortby=None, search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        user = request.env.user
        domain = []
        is_admin = request.env['res.users'].browse(user.id)._is_admin()

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc'},
            'name': {'label': _('Subject'), 'order': 'name'},
        }
        searchbar_inputs = {
            'content': {'input': 'content', 'label': _('Search <span class="nolabel"> (in Content)</span>')},
            'message': {'input': 'message', 'label': _('Search in Messages')},
            'customer': {'input': 'customer', 'label': _('Search in Customer')},
            'id': {'input': 'id', 'label': _('Search ID')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('id', 'all'):
                search_domain = OR([search_domain, [('id', 'ilike', search)]])
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, ['|', ('name', 'ilike', search), ('description', 'ilike', search)]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('partner_id', 'ilike', search)]])
            if search_in in ('message', 'all'):
                search_domain = OR([search_domain, [('message_ids.body', 'ilike', search)]])
            domain += search_domain
        if is_admin:
            calender_list = request.env['calendar.event'].search([])
            calender_ids= [i.id for i in calender_list if i.doctore_id]
            domain += [('id', 'in', calender_ids)]
            appointments = request.env['calendar.event'].search(domain)
        else:
            appointments = request.env['calendar.event'].sudo().search([('doctore_id','=',user.partner_id.id)])
        values.update({
            'appointments': appointments,
            })

        return request.render("doctor_appointment_booking_advance_axis.portal_appointment_layout",values)

    @http.route([
        '/my/appointment/<int:appointment_id>'
    ], type='http', auth="user", website=True)
    def appointments_followup(self, appointment_id=None, **kw):
        appointment = request.env['calendar.event'].sudo().search([('id', '=', int(appointment_id))])
        values = self._prepare_portal_layout_values()
        date_end = appointment.start + relativedelta(hours=appointment.duration)
        start_time = appointment.start.time()
        end_time = date_end.time()
        appointment_description = request.env['res.partner'].search([('name','=',appointment.name)])
        values.update({
            'appointment': appointment,
            'start_time': start_time,
            'end_time': end_time,
            'appointment_description':appointment_description.appointment_group_ids.product_template_id.description
            })
        return request.render("doctor_appointment_booking_advance_axis.appointments_followup",values)        
