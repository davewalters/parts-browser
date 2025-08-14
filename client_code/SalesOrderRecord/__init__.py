from ._anvil_designer import SalesOrderRecordTemplate
from anvil import *
import anvil.server
from datetime import date, datetime

class SalesOrderRecord(SalesOrderRecordTemplate):
  def __init__(self, order_id, **props):
    self.init_components(**props)
    self.order_id = order_id
    self.order = {}
    self._cust_map = {}   # name -> id

    # Button roles (optional)
    self.button_back.role = "mydefault-button"
    self.button_save.role = "save-button"
    self.button_confirm.role = "new-button"
    self.button_cancel.role = "delete-button"
    self.button_add_line.role = "new-button"

    self._load()

  # ---------- helpers ----------
  def _fmt_date(self, d):
    """Accept datetime/date/ISO string and return YYYY-MM-DD."""
    try:
      if isinstance(d, (datetime, date)):
        return d.strftime("%Y-%m-%d")
      if isinstance(d, str):
        return d.split("T")[0]
    except Exception:
      pass
    return "–"

  def _set_enabled(self, enabled: bool):
    """Enable/disable all editable widgets in one place."""
    widgets = [
      getattr(self, "drop_down_customer", None),
      getattr(self, "text_area_notes", None),
      getattr(self, "button_add_line", None),
      getattr(self, "text_box_part_id", None),
      getattr(self, "text_box_qty", None),
      getattr(self, "date_line_req", None),
    ]
    for w in widgets:
      if w is not None and hasattr(w, "enabled"):
        w.enabled = enabled

  def _call(self, name, *args, **kwargs):
    """Expect {"ok":..., "data": ...}. Raise on error; return data on success."""
    resp = anvil.server.call(name, *args, **kwargs)
    if not resp or not resp.get("ok", False):
      raise RuntimeError((resp or {}).get("error", f"{name} failed"))
    return resp["data"]

  # ---------- load & bind ----------
  def _load(self):
    # fetch order
    self.order = self._call("so_get", self.order_id)

    # dropdown choices first
    choices = self._call("so_get_customer_choices")  # [{_id, customer_name}]
    self._cust_map = {c.get("customer_name",""): c.get("_id","") for c in (choices or [])}
    self.drop_down_customer.items = list(self._cust_map.keys())

    # header
    self.label_so_id.text     = self.order.get("_id","")
    self.label_status.text    = (self.order.get("status","") or "").upper()
    self.label_order_date.text= self._fmt_date(self.order.get("order_date"))

    # customer selection + id label
    current_name = self.order.get("customer_name") or ""
    self.drop_down_customer.selected_value = current_name if current_name in self._cust_map else None
    self.label_customer_id.text = self._cust_map.get(current_name, self.order.get("customer_id",""))

    # ship-to (read-only, pulled live)
    self._refresh_ship_to(self.label_customer_id.text)

    # notes
    self.text_area_notes.text = self.order.get("notes","")

    # lines list
    self.repeating_panel_lines.items = self.order.get("lines", []) or []

    # totals
    a = self.order.get("amounts", {}) or {}
    self.label_subtotal.text = f"{float(a.get('subtotal', 0.0) or 0.0):.2f}"
    self.label_tax.text      = f"{float(a.get('tax', 0.0) or 0.0):.2f}"
    self.label_shipping.text = f"{float(a.get('shipping', 0.0) or 0.0):.2f}"
    self.label_grand.text    = f"{float(a.get('grand_total', 0.0) or 0.0):.2f}"

    # editability (draft only)
    is_draft = ((self.order.get("status") or "").strip().lower() == "draft")
    self._set_enabled(is_draft)

    # clear quick-entry after reload
    self._clear_quick_entry()

  def _refresh_ship_to(self, customer_id: str):
    try:
      if not customer_id:
        self.label_ship_to.text = ""
        return
      cust = self._call("so_get_customer_by_id", customer_id) or {}
      self.label_ship_to.text = cust.get("shipping_address", "") or ""
    except Exception as ex:
      print(f"ship_to load failed: {ex}")
      self.label_ship_to.text = ""

  def _clear_quick_entry(self):
    if hasattr(self, "text_box_part_id"):
      self.text_box_part_id.text = ""
    if hasattr(self, "text_box_qty"):
      self.text_box_qty.text = ""
    if hasattr(self, "label_part_desc"):
      self.label_part_desc.text = ""
    if hasattr(self, "label_uom"):
      self.label_uom.text = ""
    if hasattr(self, "label_unit_price"):
      self.label_unit_price.text = ""
    if hasattr(self, "date_line_req"):
      self.date_line_req.date = None

  # ---------- header events ----------
  def drop_down_customer_change(self, **e):
    name = self.drop_down_customer.selected_value or ""
    cust_id = self._cust_map.get(name, "")
    self.label_customer_id.text = cust_id
    self._refresh_ship_to(cust_id)
    # Persist on Save (not immediately)

  def _save_header(self):
    payload = {
      "notes": self.text_area_notes.text or ""
    }
    name = self.drop_down_customer.selected_value or ""
    cust_id = self._cust_map.get(name, "")
    if name and cust_id:
      payload["customer_name"] = name
      payload["customer_id"] = cust_id
    self.order = self._call("so_update", self.order_id, payload)

  def button_save_click(self, **e):
    try:
      self._save_header()
      self._load()
      Notification("Saved.", style="success").show()
    except Exception as ex:
      Notification(f"Save failed: {ex}", style="warning").show()

  def button_confirm_click(self, **e):
    try:
      self.order = self._call("so_confirm", self.order_id)
      self._load()
      Notification("Order confirmed.", style="success").show()
    except Exception as ex:
      Notification(f"Confirm failed: {ex}", style="warning").show()

  def button_cancel_click(self, **e):
    try:
      self.order = self._call("so_cancel", self.order_id)
      self._load()
      Notification("Order cancelled.", style="success").show()
    except Exception as ex:
      Notification(f"Cancel failed: {ex}", style="warning").show()

  def button_back_click(self, **e):
    open_form("SalesOrderRecords")

  # ---------- quick line entry on parent ----------
  def text_box_part_id_pressed_enter(self, **e):
    pid = (self.text_box_part_id.text or "").strip()
    if not pid:
      return
    try:
      snap = self._call("so_get_part_snapshot", pid) or {}
      self.label_part_desc.text   = snap.get("description","")
      self.label_uom.text         = snap.get("uom","ea")
      self.label_unit_price.text  = f"{float(snap.get('sell_price',0.0) or 0.0):.2f}"
      self.text_box_qty.focus()
    except Exception as ex:
      Notification(str(ex), style="warning").show()
      self.label_part_desc.text = ""
      self.label_uom.text = ""
      self.label_unit_price.text = ""

  def text_box_qty_pressed_enter(self, **e):
    self.button_add_line_click()

  def button_add_line_click(self, **e):
    try:
      pid = (self.text_box_part_id.text or "").strip()
      qty = float(self.text_box_qty.text or 0)
      rsd = self.date_line_req.date if hasattr(self, "date_line_req") else None
      if not pid or qty <= 0:
        raise RuntimeError("Enter a valid Part ID and Quantity.")

      payload = {"part_id": pid, "qty_ordered": qty, "requested_ship_date": rsd}
      self._call("so_add_line", self.order_id, payload)

      # Reload (lines + totals) and clear fields
      self._load()
      self.text_box_part_id.focus()

    except Exception as ex:
      Notification(f"Add line failed: {ex}", style="warning").show()




