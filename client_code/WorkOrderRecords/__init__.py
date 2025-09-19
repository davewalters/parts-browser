# client_code/WorkOrderRecords/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import WorkOrderRecordsTemplate
from ..WorkOrderRow import WorkOrderRow

class WorkOrderRecords(WorkOrderRecordsTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)

    self.drop_down_status.items = ["", "planned", "released", "complete", "closed"]

    self.text_wo_prefix.set_event_handler('pressed_enter', self.update_filter)
    self.text_sales_order_id.set_event_handler('pressed_enter', self.update_filter)
    self.text_date_from.set_event_handler('pressed_enter', self.update_filter)
    self.text_date_to.set_event_handler('pressed_enter', self.update_filter)
    self.drop_down_status.set_event_handler('change', self.update_filter)

    self.repeating_panel_work_orders.item_template = WorkOrderRow
    self.repeating_panel_work_orders.set_event_handler("x-open-wo", self._open_wo)
    self.repeating_panel_work_orders.set_event_handler("x-refresh", self.update_filter)

    self.button_new_work_order.role = "new-button"

    self.update_filter()

  def _parse_date(self, s):
    s = (s or "").strip()
    return s if s else None

  def update_filter(self, **e):
    status = self.drop_down_status.selected_value or ""
    date_from = self._parse_date(self.text_date_from.text)
    date_to = self._parse_date(self.text_date_to.text)
    sales_order_id = (self.text_sales_order_id.text or "").strip()

    try:
      rows = anvil.server.call(
        "wo_list",
        status=status,
        date_from=date_from,
        date_to=date_to,
        sales_order_id=sales_order_id or ""
      ) or []
      prefix = (self.text_wo_prefix.text or "").strip()
      if prefix:
        rows = [r for r in rows if str(r.get("_id","")).startswith(prefix)]
      self.repeating_panel_work_orders.items = rows
      self.label_count.text = f"{len(rows)} work orders"
    except Exception as ex:
      self.label_count.text = f"Error: {ex}"
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

