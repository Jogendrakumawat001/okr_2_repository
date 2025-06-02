/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { useService } from "@web/core/utils/hooks";

/**
 * Custom ListController for Stock Move Lines to handle serial number assignment
 * via a custom button in the list view.
 */
class StockMoveLineController extends ListController {
    setup() {
        super.setup();
        // Initialize ORM service to perform RPC calls
        this.orm = useService("orm");
        this.actionService = useService("action");
    }

    /**
     * Handler for the "Assign Serial Numbers" button click.
     * - Retrieves move lines based on the current domain
     * - Calls a server-side method to assign serial numbers
     * - Reloads the list view model after completion
     */
    async onAssignSerialClick() {
        const domain = this.model.root.domain;
        const moveLineIds = await this.orm.search("stock.move.line", domain);
        if (moveLineIds.length) {
            await this.orm.call("stock.move.line", "action_assign_serial_numbers", [moveLineIds]);
            this.model.load();  // Reload the view to reflect updates
        }
    }

    onCloseClick() {
        this.actionService.doAction({'type': 'ir.actions.act_window_close'})
    }
}

// Register the custom controller with a unique view type identifier
registry.category("views").add("stock_move_line_serial_view", {
    ...listView,
    Controller: StockMoveLineController,
    buttonTemplate: "button_assign_lot_number.ListView.Buttons",  // Template must define the button
});
