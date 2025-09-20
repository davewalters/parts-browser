# client_code/WorkOrderRecords/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import WorkOrderRecordsTemplate
from datetime import date, datetime

class WorkOrderRecords(WorkOrderRecordsTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)

    self.drop_down_status.items = ["", "planned", "released", "complete", "closed"]

    self.text_wo_prefix.set_event_handler('pressed_enter', self.update_filter)
    self.text_sales_order_id.set_event_handler('pressed_enter', self.update_filter)
    self.date_from.set_event_handler('change', self.update_filter)
    self.date_to.set_event_handler('change', self.update_filter)
    self.drop_down_status.set_event_handler('change', self.update_filter)

    self.repeating_panel_work_orders.item_template = WorkOrderRow
    self.repeating_panel_work_orders.set_event_handler("x-open-wo", self._open_wo)
    self.repeating_panel_work_orders.set_event_handler("x-refresh", self.update_filter)

    self.button_new_work_order.role = "new-button"

    self.update_filter()

  def _parse_date(self, s):
    s = (s or "").strip()
    return s if s else None

  def update_filter(self, **event_args):
    try:
      results = anvil.server.call(
        "wo_list_advanced",
        status=self.drop_down_status.selected_value or "",
        date_from=self.date_from.date,
        date_to=self.date_to.date,
        sales_order_id=self.text_sales_order_id.text or "",
      )
      self.repeating_panel_work_orders.items = results
      self.label_count.text = f"{len(results)} work orders returned"
    except Exception as e:
      self.label_count.text = f"Error: {e}"
      self.repeating_panel_work_orders.items = []

  def _open_wo(self, wo_id, **e):
    from ..WorkOrderRecord import WorkOrderRecord
    open_form("WorkOrderRecord", wo_id=wo_id, is_new=False)

  def button_new_work_order_click(self, **e):
    try:
      wo_id = anvil.server.call("work_orders_next_id")  # reserve an id
      from ..WorkOrderRecord import WorkOrderRecord
      # Navigate to the detail form in "new" mode (no DB write yet)
      open_form("WorkOrderRecord", wo_id=wo_id, is_new=True)
    except Exception as ex:
      alert(f"Unable to start a new Work Order: {ex}")

