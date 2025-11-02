from ._anvil_designer import SalesOrderRecordsTemplate
from anvil import *
import anvil.server
from datetime import date, datetime

class SalesOrderRecords(SalesOrderRecordsTemplate):
  def __init__(self, **props):
    self.init_components(**props)

    # Roles
    self.button_new_so.role = "new-button"
    self.button_back.role = "mydefault-button"
    self.repeating_panel_orders.role = "scrolling-panel"

    # Filter widgets
    self.drop_down_status.items = ["", "draft", "confirmed", "cancelled"]
    self.drop_down_status.selected_value = ""

    # UI date display (NZ-style)
    if hasattr(self.date_from, "format"):
      self.date_from.format = "DD/MM/yyyy"
    if hasattr(self.date_to, "format"):
      self.date_to.format = "DD/MM/yyyy"

    # Defaults: first day of current month → today (as you intended)
    today = date.today()
    self.date_to.date = today
    self.date_from.date = today.replace(day=1)

    # Initial load with defaults
    self.update_filter(initial=True)

  # ---------- Utilities ----------
  def format_date(self, d):
    """Render server 'order_date' which may be a datetime or ISO string."""
    try:
      if isinstance(d, (datetime, date)):
        return d.strftime("%Y-%m-%d")  # fixed directives
      if isinstance(d, str):
        return d.split("T")[0]         # ISO → YYYY-MM-DD
    except Exception:
      return "–"
    return "–"

  def _collect_filter_args(self):
    return dict(
    so_id_prefix=(self.text_box_so_id_prefix.text or "").strip(),
    customer_name=(self.text_box_customer.text or "").strip(),
    status=(self.drop_down_status.selected_value or ""),
    # send date objects directly; NOT .isoformat()
    from_date=self.date_from.date,
    to_date=self.date_to.date,
    limit=500
  )

  # ---------- Filter/apply ----------
  def update_filter(self, initial=False, **e):
    rows = anvil.server.call("sales_order_list", **self._collect_filter_args())
    rows = rows or []

    # Display-only fields
    for r in rows:
      r["_order_date_display"] = self.format_date(r.get("order_date"))

    self.repeating_panel_orders.items = rows
    self.label_count.text = f"{len(rows)} sales order(s) returned"

    if not initial and not rows:
      Notification("No sales orders found for the current filter.", style="warning").show()

  # ---------- Filter events ----------
  # Text boxes: update on Enter (per your preference)
  def text_box_so_id_prefix_pressed_enter(self, **event_args):
    self.update_filter()

  def text_box_customer_pressed_enter(self, **event_args):
    self.update_filter()

  # Drop-down + DatePickers: dynamic update on change
  def drop_down_status_change(self, **event_args):
    self.update_filter()

  def date_from_change(self, **event_args):
    self.update_filter()

  def date_to_change(self, **event_args):
    self.update_filter()

  # ---------- Actions ----------
  def button_new_so_click(self, **event_args):
    new_so = anvil.server.call("sales_order_create", {"notes": ""})
    if not new_so:
      Notification("Create failed.", style="warning").show()
      return
    open_form("SalesOrderRecord", order_id=new_so["_id"])

  def button_back_click(self, **event_args):
    open_form("Nav")



