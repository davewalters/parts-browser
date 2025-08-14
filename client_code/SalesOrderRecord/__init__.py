# client_code/SalesOrderRecord/__init__.py
from ._anvil_designer import SalesOrderRecordTemplate
from anvil import *
import anvil.server
from datetime import date

class SalesOrderRecord(SalesOrderRecordTemplate):
  def __init__(self, order_id, **props):
    self.init_components(**props)
    self.order_id = order_id

    self.button_back.role = "mydefault-button"
    self.button_save.role = "save-button"
    self.button_confirm.role = "new-button"
    self.button_cancel.role = "delete-button"
    self.button_add_line.role = "new-button"
    
    self._cust_map = {}  # name -> id
    self._load()

  # -------- helpers --------
  def _fmt_date(self, d):
    try:
      return d.strftime("%Y-%m-%d")
    except Exception:
      return str(d) if d else ""

  def _load_customer_choices(self):
    try:
      choices = anvil.server.call("get_customer_choices")  # [{_id, customer_name}]
      self._cust_map = {c.get("customer_name",""): c.get("_id","") for c in choices}
      self.drop_down_customer.items = list(self._cust_map.keys())
    except Exception as ex:
      self._cust_map = {}
      self.drop_down_customer.items = []
      print(f"get_customer_choices not available yet: {ex}")

  def _load_customer_details(self, customer_id: str):
    """Fetch live customer data and populate read-only labels."""
    if not customer_id:
      self.label_ship_to.text = ""
      # add other labels here if needed (email, phone, etc.)
      return
    try:
      cust = anvil.server.call("get_customer_by_id", customer_id)
      # Expecting something like:
      # {"_id":"CUST0001","customer_name":"Acme","shipping_address":"...","billing_address":"...","email":"..."}
      ship = (cust or {}).get("shipping_address", "")
      # You can format multi-line addresses nicely if stored as a dict; for strings just render directly.
      self.label_ship_to.text = ship or ""

    except Exception as ex:
      print(f"get_customer_by_id not available yet: {ex}")
      self.label_ship_to.text = ""

  def _load(self):
    self.order = anvil.server.call("so_get", self.order_id)
    if not self.order:
      Notification("Sales order not found.", style="warning").show()
      return

    # customers dropdown
    self._load_customer_choices()

    # header
    self.label_so_id.text = self.order.get("_id","")
    self.label_status.text = (self.order.get("status") or "").upper()
    self.label_order_date.text = self._fmt_date(self.order.get("order_date"))
    current_name = self.order.get("customer_name") or ""
    self.drop_down_customer.selected_value = current_name if current_name in self._cust_map else None
    self.label_customer_id.text = self._cust_map.get(current_name, self.order.get("customer_id",""))

    # fetch live customer-derived fields, display-only
    self._load_customer_details(self.label_customer_id.text)

    self.text_area_notes.text = self.order.get("notes","")

    # lines
    self.repeating_panel_lines.items = self.order.get("lines", [])

    # totals
    a = self.order.get("amounts", {})
    self.label_subtotal.text = f"{a.get('subtotal',0.0):.2f}"
    self.label_tax.text = f"{a.get('tax',0.0):.2f}"
    self.label_shipping.text = f"{a.get('shipping',0.0):.2f}"
    self.label_grand.text = f"{a.get('grand_total',0.0):.2f}"

    # editability
    editable = (self.order.get("status") == "draft")
    self.drop_down_customer.enabled = editable
    self.text_area_notes.enabled = editable
    self.button_add_line.enabled = editable

  # -------- header events --------
  def drop_down_customer_change(self, **e):
    name = self.drop_down_customer.selected_value or ""
    cust_id = self._cust_map.get(name, "")
    self.label_customer_id.text = cust_id
    # refresh display-only customer details from Customers collection
    self._load_customer_details(cust_id)
    # don't persist yet; Save will persist header

  def _save_header(self):
    payload = {
      "notes": self.text_area_notes.text or ""
    }
    name = self.drop_down_customer.selected_value or ""
    cust_id = self._cust_map.get(name, "")
    if name and cust_id:
      # Only persist the references (id/name). No customer fields are written into the order.
      payload["customer_name"] = name
      payload["customer_id"] = cust_id
    self.order = anvil.server.call("update_sales_order", self.order_id, payload)

  def button_save_click(self, **e):
    try:
      self._save_header()
      self._load()
      Notification("Saved.", style="success").show()
    except Exception as ex:
      Notification(f"Save failed: {ex}", style="warning").show()

  def button_confirm_click(self, **e):
    try:
      self.order = anvil.server.call("confirm_sales_order", self.order_id)
      self._load()
      Notification("Order confirmed.", style="success").show()
    except Exception as ex:
      Notification(f"Confirm failed: {ex}", style="warning").show()

  def button_cancel_click(self, **e):
    try:
      self.order = anvil.server.call("cancel_sales_order", self.order_id)
      self._load()
      Notification("Order cancelled.", style="success").show()
    except Exception as ex:
      Notification(f"Cancel failed: {ex}", style="warning").show()

  def button_back_click(self, **e):
    open_form("SalesOrderRecords")

  # -------- quick line entry (unchanged in spirit) --------
  def text_box_part_id_pressed_enter(self, **e):
    pid = (self.text_box_part_id.text or "").strip()
    if not pid: return
    try:
      snap = anvil.server.call("get_part_snapshot", pid)
      self.label_part_desc.text = snap.get("description","")
      self.label_uom.text = snap.get("uom","ea")
      self.label_unit_price.text = f"{float(snap.get('sell_price',0.0)):.2f}"
      self.text_box_qty.focus()
    except Exception as ex:
      Notification(str(ex), style="warning").show()
      self.label_part_desc.text = ""
      self.label_uom.text = ""
      self.label_unit_price.text = ""

  def button_add_line_click(self, **e):
    try:
      payload = {
        "part_id": (self.text_box_part_id.text or "").strip(),
        "qty_ordered": float(self.text_box_qty.text or 0),
        "requested_ship_date": self.date_line_req.date
      }
      anvil.server.call("add_sales_order_line", self.order_id, payload)
      self._load()
      # clear
      self.text_box_part_id.text = ""
      self.text_box_qty.text = ""
      self.label_part_desc.text = ""
      self.label_uom.text = ""
      self.label_unit_price.text = ""
      self.date_line_req.date = None
      self.text_box_part_id.focus()
    except Exception as ex:
      Notification(f"Add line failed: {ex}", style="warning").show()


