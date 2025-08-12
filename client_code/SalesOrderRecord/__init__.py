# client_code/SalesOrderRecord/__init__.py
from ._anvil_designer import SalesOrderRecordTemplate
from anvil import *
import anvil.server
from datetime import date

class SalesOrderRecord(SalesOrderRecordTemplate):
  def __init__(self, order_id, **props):
    self.init_components(**props)
    self.order_id = order_id

    # Button roles
    self.button_back.role = "mydefault-button"
    self.button_save.role = "save-button"
    self.button_confirm.role = "primary-color"
    self.button_cancel.role = "delete-button"
    self.button_add_line.role = "new-button"
    # Internal map: customer_name -> customer_id
    self._cust_map = {}

    self._load()

  # ---------- Load ----------
  def _load(self):
    self.order = anvil.server.call("get_sales_order", self.order_id)
    if not self.order:
      Notification("Sales order not found.", style="warning").show()
      return

    # Load customer names for dropdown (names only; id shown in label)
    try:
      choices = anvil.server.call("get_customer_choices")  # [{_id, customer_name}]
      self._cust_map = {c.get("customer_name",""): c.get("_id","") for c in choices}
      # Items are names only
      self.drop_down_customer.items = list(self._cust_map.keys())
    except Exception as ex:
      self._cust_map = {}
      self.drop_down_customer.items = []
      print(f"get_customer_choices not available yet: {ex}")

    # Header bindings
    self.label_so_id.text = self.order.get("_id", "")
    self.label_status.text = (self.order.get("status") or "").upper()

    # Select current customer by name (if present)
    current_name = self.order.get("customer_name") or ""
    self.drop_down_customer.selected_value = current_name if current_name in self._cust_map else None
    # Set customer_id label from map (or from order as fallback)
    mapped_id = self._cust_map.get(current_name, "")
    self.label_customer_id.text = mapped_id or self.order.get("customer_id", "")

    self.date_order_date.date = self.order.get("order_date") or date.today()
    self.label_order_date = self.date_order_date.date
    self.text_area_notes.text = self.order.get("notes", "")

    # Lines
    self.repeating_panel_lines.items = self.order.get("lines", [])

    # Totals
    a = self.order.get("amounts", {})
    self.label_subtotal.text = f"{a.get('subtotal', 0.0):.2f}"
    self.label_tax.text = f"{a.get('tax', 0.0):.2f}"
    self.label_shipping.text = f"{a.get('shipping', 0.0):.2f}"
    self.label_grand.text = f"{a.get('grand_total', 0.0):.2f}"

    # Editing rules
    editable = (self.order.get("status") == "draft")
    self.drop_down_customer.enabled = editable
    self.date_order_date.enabled = editable
    self.text_area_notes.enabled = editable
    self.button_add_line.enabled = editable

    # Clear quick-entry labels if needed
    if not editable:
      self._clear_quick_entry_labels()

  def _clear_quick_entry_labels(self):
    self.label_part_desc.text = ""
    self.label_uom.text = ""
    self.label_unit_price.text = ""

  # ---------- Header events ----------
  def drop_down_customer_change(self, **event_args):
    """Choose by name; show id label; persist on Save."""
    name = self.drop_down_customer.selected_value or ""
    cust_id = self._cust_map.get(name, "")
    self.label_customer_id.text = cust_id

  def _save_header(self):
    # Persist selection and header fields (only in draft)
    payload = {
      "order_date": self.date_order_date.date or date.today(),
      "notes": self.text_area_notes.text or ""
    }
    # Include both name and id based on dropdown
    name = self.drop_down_customer.selected_value or ""
    cust_id = self._cust_map.get(name, "")
    if name and cust_id:
      payload["customer_name"] = name
      payload["customer_id"] = cust_id

    self.order = anvil.server.call("update_sales_order", self.order_id, payload)

  def button_save_click(self, **event_args):
    try:
      self._save_header()
      self._load()
      Notification("Saved.", style="success").show()
    except Exception as ex:
      Notification(f"Save failed: {ex}", style="warning").show()

  def button_confirm_click(self, **event_args):
    try:
      self.order = anvil.server.call("confirm_sales_order", self.order_id)
      self._load()
      Notification("Order confirmed.", style="success").show()
    except Exception as ex:
      Notification(f"Confirm failed: {ex}", style="warning").show()

  def button_cancel_click(self, **event_args):
    try:
      self.order = anvil.server.call("cancel_sales_order", self.order_id)
      self._load()
      Notification("Order cancelled.", style="success").show()
    except Exception as ex:
      Notification(f"Cancel failed: {ex}", style="warning").show()

  def button_back_click(self, **event_args):
    open_form("SalesOrderRecords")

  # ---------- Quick line entry ----------
  def text_box_part_id_pressed_enter(self, **event_args):
    """Fetch desc / UOM / price from parts; price not editable."""
    pid = (self.text_box_part_id.text or "").strip()
    if not pid:
      return
    try:
      snap = anvil.server.call("get_part_snapshot", pid)
      self.label_part_desc.text = snap.get("description", "")
      self.label_uom.text = snap.get("uom", "ea")
      self.label_unit_price.text = f"{float(snap.get('sell_price', 0.0)):.2f}"
      self.text_box_qty.focus()
    except Exception as ex:
      Notification(str(ex), style="warning").show()
      self._clear_quick_entry_labels()

  def button_add_line_click(self, **event_args):
    try:
      payload = {
        "part_id": (self.text_box_part_id.text or "").strip(),
        "qty_ordered": float(self.text_box_qty.text or 0),
        # Optionally send requested_ship_date; server may ignore
        "requested_ship_date": self.date_line_req.date
      }
      # Server should derive description / uom / unit_price from part
      anvil.server.call("add_sales_order_line", self.order_id, payload)

      self._load()
      # Clear for next entry
      self.text_box_part_id.text = ""
      self.text_box_qty.text = ""
      self.date_line_req.date = None
      self._clear_quick_entry_labels()
      self.text_box_part_id.focus()
    except Exception as ex:
      Notification(f"Add line failed: {ex}", style="warning").show()

