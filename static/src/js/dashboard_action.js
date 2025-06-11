/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, useState, onWillStart, onMounted } = owl;
import { rpc } from "@web/core/network/rpc";
import { Domain } from "@web/core/domain";
import { _t } from "@web/core/l10n/translation";
import { serializeDate, serializeDateTime } from "@web/core/l10n/dates";

const today = new Date();
const day = String(today.getDate()).padStart(2, '0');
const month = String(today.getMonth() + 1).padStart(2, '0');
const year = today.getFullYear();
const formattedDate = `${year}-${month}-${day}`;

class RoomStatusDashboard extends Component {
    setup() {
        console.log('RoomStatusDashboard setup - props:', this.props);
        this.room_categories = this.props.room_categories;
    }
}
RoomStatusDashboard.template = 'RoomStatusDashboard';
RoomStatusDashboard.props = {
    room_categories: { type: Array },
};

export class CustomDashBoard extends Component {
    setup() {
        console.log('CustomDashBoard setup');
        this.state = useState({
            room_categories: [],
            total_room: 0,
            available_room: 0,
            staff: 0,
            check_in: 0,
            reservation: 0,
            check_out: 0,
            total_vehicle: 0,
            available_vehicle: 0,
            total_event: 0,
            today_events: 0,
            pending_events: 0,
            food_items: 0,
            food_order: 0,
            total_revenue: '',
            today_revenue: '',
            month_revenue: '',
            year_revenue: '',
            pending_payment: '',
        });
        
        this.action = useService("action");
        this.orm = useService("orm");
        onWillStart(this.onWillStart);
        onMounted(this.onMounted);
    }

    async onWillStart() {
        await this.fetch_data();
    }

    async onMounted() {
        // Component mounted
    }

    async fetch_data() {
        try {
            console.log('Fetching dashboard data...');
            // Fetch dashboard data
            const dashboardData = await rpc('/web/dataset/call_kw/room.booking/get_details', {
                model: 'room.booking',
                method: 'get_details',
                args: [{}],
                kwargs: {},
            });
            console.log('Dashboard data received:', dashboardData);

            // Update state with dashboard data
            Object.assign(this.state, {
                total_room: dashboardData.total_room,
                available_room: dashboardData.available_room,
                staff: dashboardData.staff,
                check_in: dashboardData.check_in,
                reservation: dashboardData.reservation,
                check_out: dashboardData.check_out,
                total_vehicle: dashboardData.total_vehicle,
                available_vehicle: dashboardData.available_vehicle,
                total_event: dashboardData.total_event,
                today_events: dashboardData.today_events,
                pending_events: dashboardData.pending_events,
                food_items: dashboardData.food_items,
                food_order: dashboardData.food_order,
            });

            // Format currency values
            const currency_symbol = dashboardData.currency_symbol;
            const currency_position = dashboardData.currency_position;
            
            ['total_revenue', 'today_revenue', 'month_revenue', 'year_revenue', 'pending_payment'].forEach(field => {
                this.state[field] = currency_position === 'after' 
                    ? `${dashboardData[field]} ${currency_symbol}`
                    : `${currency_symbol} ${dashboardData[field]}`;
            });

            // Fetch room categories
            console.log('Fetching room categories...');
            const roomCategories = await this.orm.call(
                'hotel.room.category',
                'get_rooms_by_category',
                [],
                {}
            );
            console.log('Room categories received:', roomCategories);
            this.state.room_categories = roomCategories;

        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        }
    }

    total_rooms(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
                this.action.doAction({
                    name: _t("Rooms"),
                    type:'ir.actions.act_window',
                    res_model:'product.template',
                    view_mode:'list,form',
                    view_type:'form',
                    views:[[false,'list'],[false,'form']],
                    domain: [['is_roomtype', '=', true]],
                    target:'current'
                },options)
    }
    check_ins(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
        this.action.doAction({
            name: _t("Check-In"),
            type:'ir.actions.act_window',
            res_model:'room.booking',
            view_mode:'list,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [['state', '=', 'check_in']],
            target:'current'
        },options)
    }
    //    Total Events
    view_total_events(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
        this.action.doAction({
            name: _t("Total Events"),
            type:'ir.actions.act_window',
            res_model:'event.event',
            view_mode:'kanban,list,form',
            view_type:'form',
            views:[[false,'kanban'],[false,'list'],[false,'form']],
            domain: [],
            target:'current'
        },options)
    }
    //        //    Today's Events
    fetch_today_events(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
        this.action.doAction({
            name: _t("Today's Events"),
            type:'ir.actions.act_window',
            res_model:'event.event',
            view_mode:'kanban,list,form',
            view_type:'form',
            views:[[false,'kanban'],[false,'list'],[false,'form']],
            domain:  [['date_end', '=', formattedDate]],
            target:'current'
        },options)
    }
    //        //    Pending Events
    fetch_pending_events(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
        this.action.doAction({
            name: _t("Pending Events"),
            type:'ir.actions.act_window',
            res_model:'event.event',
            view_mode:'kanban,list,form',
            view_type:'form',
            views:[[false,'kanban'],[false,'list'],[false,'form']],
            domain:  [['date_end', '>=', formattedDate]],
            target:'current'
        },options)
    }
    //        //    Total staff
    fetch_total_staff(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
        this.action.doAction({
            name: _t("Total Staffs"),
            type:'ir.actions.act_window',
            res_model:'res.users',
            view_mode:'list,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [['groups_id.name', 'in',['Admin',
                       'Cleaning Team User',
                       'Cleaning Team Head',
                       'Receptionist',
                       'Maintenance Team User',
                       'Maintenance Team Leader'
                   ]]],
            target:'current'
        },options)
    }
    //    check-out
    check_outs(e){
        var self = this;
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
        this.action.doAction({
            name: _t("Today's Check-Out"),
            type:'ir.actions.act_window',
            res_model:'room.booking',
            view_mode:'list,form',
            view_type:'list,form',
            views:[[false,'list'],[false,'form']],
            domain: [['state', '=', 'check_out']],
            target:'current'
        },options)
    }
    //    Available rooms
    available_rooms(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
        this.action.doAction({
            name: _t("Available Room"),
            type:'ir.actions.act_window',
            res_model:'product.template',
            view_mode:'list,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [['status', '=', 'available'],['is_roomtype', '=', true]],
            target:'current'
        },options)
    }
    //    Reservations
    reservations(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
        this.action.doAction({
            name: _t("Total Reservations"),
            type:'ir.actions.act_window',
            res_model:'room.booking.line',
            view_mode:'list,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [['state', '=', 'reserved']],
            target:'current'
        },options)
    }
    //    Food Items
    fetch_food_item(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
        this.action.doAction({
            name: _t("Food Items"),
            type:'ir.actions.act_window',
            res_model:'product.template',
            view_mode:'list,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [['is_foodtype', '=', true]],
            target:'current'
        },options)
    }
    //    food Orders
    async fetch_food_order(e){
        var self = this;
        const result = await this.orm.call('food.booking.line', 'search_food_orders',[{}],{});
        e.stopPropagation();
        e.preventDefault();
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
        this.action.doAction({
            name: _t("Food Orders"),
            type:'ir.actions.act_window',
            res_model:'food.booking.line',
            view_mode:'list,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
           domain: [['id','in', result]],
            target:'current'
        },options)
    }
    //    total vehicle
    fetch_total_vehicle(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
        this.action.doAction({name: _t("Total Vehicles"),
                    type:'ir.actions.act_window',
                    res_model:'fleet.vehicle.model',
                    view_mode:'list,form',
                    view_type:'form',
                    views:[[false,'list'],[false,'form']],
                    target:'current'
                },options)
    }
    //    Available Vehicle
    async fetch_available_vehicle(e){
    const result = await this.orm.call('fleet.booking.line', 'search_available_vehicle',[{}],{});
        var self = this;
        var options={on_reverse_breadcrum:this.on_reverse_breadcrum,};
        e.stopPropagation();
        e.preventDefault();
        this.action.doAction({
            name: _t("Available Vehicle"),
            type:'ir.actions.act_window',
            res_model:'fleet.vehicle.model',
            view_mode:'list,form',
            view_type:'form',
            views:[[false,'list'],[false,'form']],
            domain: [['id','not in', result]],
            target:'current'
        },options)
    }
}

CustomDashBoard.template = 'CustomDashBoard';
CustomDashBoard.components = { RoomStatusDashboard };

registry.category("actions").add("custom_dashboard_tags", CustomDashBoard);