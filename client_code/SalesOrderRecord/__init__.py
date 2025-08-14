# client_code/SalesOrderRecord/__init__.py
# client_code/SalesOrderRecord/__init__.py
from ._anvil_designer import SalesOrderRecordTemplate
from anvil import *
import anvil.server
from datetime import date, datetime

class SalesOrderRecord(SalesOrderRecordTemplate):
  def __init__(self, order_id, **props):
    self.init_components(**props)
    self.order_id = order_id
    self.order = {}

    # roles (optional)
    self.button_back.role = "mydefault-button"
    self.button_save.role = "save-button"
    self.button_confirm.role = "new-button"
    self.button_cancel.role = "delete-button"
    self.button_add_line.role = "new-button"

    # name -> id map for customers
    self._cust_map = {}

    self._load()

  # ---------- helpers ----------
  def _fmt_date(self, d):
    """Accepts datetime/date/ISO string and returns YYYY-MM-DD."""
    try:
      if isinstance(d, (datetime, date)):
        return d.strftime("%Y-%m-%d")
      if isinstance(d, str):
        return d.split("T")[0]
    except Exception:
      pass
    return "–"

  def _set_label(self, name, value):
    comp = getattr(self, name, None)
    if comp is not None:
      comp.text = value

  def _apply_editability(self, editable: bool):
    """Enable/disable all interactive widgets according to order status."""
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
        w.enabled = editable

  def _load_customer_choices(self):
    """Populate dropdown with customer names and build name->id map."""
    try:
      resp = anvil.server.call("so_get_customer_choices")
      if not resp or not resp.get("ok", False):
        raise RuntimeError((resp or {}).get("error", "get_customer_choices failed"))
      choices = resp["data"] or []  # [{_id, customer_name}]
      self._cust_map = {c.get("customer_name", ""): c.get("_id", "") for c in choices}
      self.drop_down_customer.items = list(self._cust_map.keys())
    except Exception as ex:
      self._cust_map = {}
      self.drop_down_customer.items = []
      print(f"so_get_customer_choices not available yet: {ex}")

  def _load_customer_details(self, customer_id: str):
    """Fetch live customer data and populate read-only labels (ship-to)."""
    if not customer_id:
      self.label_ship_to.text = ""
      return
    try:
      resp = anvil.server.call("so_get_customer_by_id", customer_id)
      if not resp or not resp.get("ok", False):
        raise RuntimeError((resp or {}).get("error", "get_customer_by_id failed"))
      cust = resp["data"] or {}
      ship = cust.get("shipping_address", "")  # already formatted server-side
      self.label_ship_to.text = ship or ""
    except Exception as ex:
      print(f"so_get_customer_by_id not available yet: {ex}")
      self.label_ship_to.text = ""

  # ---------- load & bind ----------
  def _load(self):
    # fetch order
    resp = anvil.server.call("so_get", self.order_id)
    if not resp or not resp.get("ok", False):
      Notification((resp or {}).get("error", "Load failed."), style="warning").show()
      return
    self.order = resp["data"] or {}

    # customers dropdown first (so selected_value can bind correctly)
    self._load_customer_choices()

    # header fields
    self._set_label("label_so_id", self.order.get("_id", ""))
    self._set_label("label_status", (self.order.get("status", "") or "").upper())
    self._set_label("label_order_date", self._fmt_date(self.order.get("order_date")))

    current_name = self.order.get("customer_name") or ""
    # bind dropdown if the name exists in choices
    self.drop_down_customer.selected_value = current_name if current_name in self._cust_map else None
    # show id (from map if we have the name; else fallback to stored id)
    self._set_label("label_customer_id", self._cust_map.get(current_name, self.order.get("customer_id", "")))

    # display-only customer-derived labels
    self._load_customer_details(self.label_customer_id.text)

    # notes
    if hasattr(self, "text_area_notes"):
      self.text_area_notes.text = self.order.get("notes", "")

    # lines
    if hasattr(self, "repeating_panel_lines"):
      lines = list(self.order.get("lines", []))
      # pass edit permission into line rows (if you later allow inline qty edits)
      is_draft = ((self.order.get("status") or "").strip().lower() == "draft")
      for l in lines:
        l["_allow_edit"] = is_draft
      self.repeating_panel_lines.items = lines

    # totals
    a = self.order.get("amounts", {}) or {}
    self._set_label("label_subtotal", f"{float(a.get('subtotal', 0.0) or 0.0):.2f}")
    self._set_label("label_tax",      f"{float(a.get('tax', 0.0) or 0.0):.2f}")
    self._set_label("label_shipping", f"{float(a.get('shipping', 0.0) or 0.0):.2f}")
    self._set_label("label_grand",    f"{float(a.get('grand_total', 0.0) or 0.0):.2f}")

    # editability by status
    is_draft = ((self.order.get("status") or "").strip().lower() == "draft")
    self._apply_editability(is_draft)

  # ---------- header events ----------
  def drop_down_customer_change(self, **e):
    name = self.drop_down_customer.selected_value or ""
    cust_id = self._cust_map.get(name, "")
    self._set_label("label_customer_id", cust_id)
    # refresh display-only customer details from Customers collection
    self._load_customer_details(cust_id)
    # don't persist yet; Save will persist header

  def _save_header(self):
    payload = {
      "notes": (self.text_area_notes.text or "") if hasattr(self, "text_area_notes") else ""
    }
    name = self.drop_down_customer.selected_value or ""
    cust_id = self._cust_map.get(name, "")
    if name and cust_id:
      # persist references only
      payload["customer_name"] = name
      payload["customer_id"] = cust_id

    resp = anvil.server.call("so_update", self.order_id, payload)
    if not resp or not resp.get("ok", False):
      raise RuntimeError((resp or {}).get("error", "Update failed"))
    self.order = resp["data"] or {}

  def button_save_click(self, **e):
    try:
      self._save_header()
      self._load()
      Notification("Saved.", style="success").show()
    except Exception as ex:
      Notification(f"Save failed: {ex}", style="warning").show()

  def button_confirm_click(self, **e):
    try:
      resp = anvil.server.call("so_confirm", self.order_id)
      if not resp or not resp.get("ok", False):
        raise RuntimeError((resp or {}).get("error", "Confirm failed"))
      self.order = resp["data"] or {}
      self._load()
      Notification("Order confirmed.", style="success").show()
    except Exception as ex:
      Notification(f"Confirm failed: {ex}", style="warning").show()

  def button_cancel_click(self, **e):
    try:
      resp = anvil.server.call("so_cancel", self.order_id)
      if not resp or not resp.get("ok", False):
        raise RuntimeError((resp or {}).get("error", "Cancel failed"))
      self.order = resp["data"] or {}
      self._load()
      Notification("Order cancelled.", style="success").show()
    except Exception as ex:
      Notification(f"Cancel failed: {ex}", style="warning").show()

  def button_back_click(self, **e):
    open_form("SalesOrderRecords")

  # ---------- quick line entry ----------
  def text_box_part_id_pressed_enter(self, **e):
    pid = (self.text_box_part_id.text or "").strip()
    if not pid:
      return
    try:
      resp = anvil.server.call("so_get_part_snapshot", pid)
      if not resp or not resp.get("ok", False):
        raise RuntimeError((resp or {}).get("error", "get_part_snapshot failed"))
      snap = resp["data"] or {}
      self.label_part_desc.text = snap.get("description", "")
      self.label_uom.text = snap.get("uom", "ea")
      self.label_unit_price.text = f"{float(snap.get('sell_price', 0.0) or 0.0):.2f}"
      if hasattr(self, "text_box_qty"):
        self.text_box_qty.focus()
    except Exception as ex:
      Notification(str(ex), style="warning").show()
      self.label_part_desc.text = ""
      self.label_uom.text = ""
      self.label_unit_price.text = ""

  def text_box_qty_pressed_enter(self, **e):
    # convenience: Enter in qty triggers add
    self.button_add_line_click()

  def button_add_line_click(self, **e):
    try:
      payload = {
        "part_id": (self.text_box_part_id.text or "").strip(),
        "qty_ordered": float(self.text_box_qty.text or 0),
        "requested_ship_date": self.date_line_req.date if hasattr(self, "date_line_req") else None
      }
      resp = anvil.server.call("so_add_line", self.order_id, payload)
      if not resp or not resp.get("ok", False):
        raise RuntimeError((resp or {}).get("error", "Add line failed"))
      # reload (totals and lines)
      self._load()
      # clear quick-entry
      self.text_box_part_id.text = ""
      self.text_box_qty.text = ""
      self.label_part_desc.text = ""
      self.label_uom.text = ""
      self.label_unit_price.text = ""
      if hasattr(self, "date_line_req"):
        self.date_line_req.date = None
      self.text_box_part_id.focus()
    except Exception as ex:
      Notification(f"Add line failed: {ex}", style="warning").show()



