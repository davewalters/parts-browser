from ._anvil_designer import SalesOrderRecordsTemplate
from anvil import *
import anvil.server
from datetime import date, datetime

class SalesOrderRecords(SalesOrderRecordsTemplate):
  def __init__(self, **props):
    self.init_components(**props)

    # Roles (optional)
    self.button_new_so.role = "new-button"
    self.button_back.role = "mydefault-button"
    self.repeating_panel_orders.role = "scrolling-panel"

    # Filter widgets
    self.drop_down_status.items = ["", "draft", "confirmed", "cancelled"]
    self.drop_down_status.selected_value = ""

    # End date initialises to today (bonus)
    self.date_to.date = date.today()
    self.date_from.date = date.today().replace(day=1)  # optional
    
    self.update_filter()  # initial load

  # ---------- Utilities ----------
  def format_date(self, d):
    """Render server 'order_date' which may be a datetime or ISO string."""
    try:
      if isinstance(d, (datetime, date)):
        return d.strftime("%Y-%m-%d")
      if isinstance(d, str):
        # ISO: '2025-08-15T08:20:34.123456+00:00' -> '2025-08-15'
        return d.split("T")[0]
    except:
      return "–"
    return "–"

  # ---------- Filter/apply ----------
  def update_filter(self, **e):
    so_prefix = (self.text_box_so_id_prefix.text or "").strip()
    cust = (self.text_box_customer.text or "").strip()
    status = self.drop_down_status.selected_value or ""
  
    fd = self.date_from.date      # date or None
    td = self.date_to.date        # date or None
  
    # Server accepts date|datetime|ISO; raw list returned
    rows = anvil.server.call(
      "so_list",
      so_id_prefix=so_prefix,
      customer_name=cust,
      status=status,
      from_date=fd.isoformat() if fd else None,
      to_date=td.isoformat() if td else None,
      limit=500
    )
  
    if not rows:
      self.repeating_panel_orders.items = []   # clear
      self.label_count.text = "0 sales order(s) returned"
      Notification("⚠️ No sales orders found.", style="warning").show()
      return
  
    # Post-process for display-only fields (optional)
    for r in rows:
      r["_order_date_display"] = self.format_date(r.get("order_date"))
  
    self.repeating_panel_orders.items = rows
    self.label_count.text = f"{len(rows)} sales order(s) returned"


  # ---------- Filter events ----------
  def text_box_so_id_prefix_pressed_enter(self, **event_args):
    self.update_filter()

  def text_box_customer_pressed_enter(self, **event_args):
    self.update_filter()

  def drop_down_status_change(self, **event_args):
    self.update_filter()

  def date_from_change(self, **event_args):
    self.update_filter()

  def date_to_change(self, **event_args):
    self.update_filter()

  # ---------- Actions ----------
  def button_new_so_click(self, **event_args):
    new_so = anvil.server.call("so_create", {"notes": ""})
    if not new_so:
      Notification("Create failed.", style="warning").show()
      return
    open_form("SalesOrderRecord", order_id=new_so["_id"])


  def button_back_click(self, **event_args):
    open_form("Nav")


