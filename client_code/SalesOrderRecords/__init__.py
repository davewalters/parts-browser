# client_code/SalesOrderRecords/__init__.py
from ._anvil_designer import SalesOrderRecordsTemplate
from anvil import *
import anvil.server
from datetime import date, datetime

class SalesOrderRecords(SalesOrderRecordsTemplate):
  def __init__(self, **props):
    self.init_components(**props)

    # roles (optional)
    self.button_new_so.role = "new-button"
    self.button_back.role = "mydefault-button"

    # initialise filters
    self.drop_down_status.items = ["", "draft", "confirmed", "cancelled"]
    self.drop_down_status.selected_value = ""

    self.date_to.date = date.today()                   # end date defaults to today
    self.date_from.date = date.today().replace(day=1)  # optional: first of month

    # load once
    self.update_filter()

  # ------------- Core filter/update -------------
  def update_filter(self, **e):
    so_prefix = (self.text_box_so_id_prefix.text or "").strip()
    cust = (self.text_box_customer.text or "").strip()
    status = self.drop_down_status.selected_value or ""

    fd = self.date_from.date
    td = self.date_to.date

    # Call uplink; returns {"ok":..., "data": ...}
    resp = anvil.server.call(
      "so_list",
      so_id_prefix=so_prefix,
      customer_name=cust,
      status=status,
      from_date=fd.isoformat() if fd else None,
      to_date=td.isoformat() if td else None,
      limit=500
    )
    if not resp["ok"]:
      Notification(resp["error"], style="warning").show()
      return

    rows = resp["data"] or []
    self.repeating_panel_orders.items = rows
    self.label_count.text = f"{len(rows)}"

  # ------------- Filter events -------------
  # TextBoxes update on Enter
  def text_box_so_id_prefix_pressed_enter(self, **event_args):
    self.update_filter()

  def text_box_customer_pressed_enter(self, **event_args):
    self.update_filter()

  # DropDown & DatePickers update on change
  def drop_down_status_change(self, **event_args):
    self.update_filter()

  def date_from_change(self, **event_args):
    self.update_filter()

  def date_to_change(self, **event_args):
    self.update_filter()

  # ------------- Actions -------------
  def button_new_so_click(self, **event_args):
    resp = anvil.server.call("so_create", {"notes": ""})
    if not resp["ok"]:
      Notification(resp["error"], style="warning").show()
      return
    new_so = resp["data"]
    open_form("SalesOrderRecord", order_id=new_so["_id"])

  def button_back_click(self, **event_args):
    open_form("Nav")

