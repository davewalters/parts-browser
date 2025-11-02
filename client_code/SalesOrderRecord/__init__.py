from ._anvil_designer import SalesOrderRecordTemplate
from anvil import *
import anvil.server
from datetime import date, datetime

class SalesOrderRecord(SalesOrderRecordTemplate):
  def __init__(self, order_id, **props):
    self.init_components(**props)
    self.order_id = order_id
    self.order = {}
    # name -> business customer_id (e.g., "C0001")
    self._cust_map = {}

    # Button roles (optional)
    self.button_back.role = "mydefault-button"
    self.button_save.role = "save-button"
    self.button_confirm.role = "new-button"
    self.button_cancel.role = "delete-button"
    self.button_add_line.role = "new-button"
    self.button_create_wos.role = "new-button"
    self.button_view_wos.role = "mydefault-button"
    self.repeating_panel_lines.role = "scrolling-panel"

    self.repeating_panel_lines.set_event_handler("x-refresh-so-line", self._refresh_so_line)
    self.repeating_panel_lines.set_event_handler("x-delete-so-line", self._delete_so_line)

    self._load()

  # ---------- helpers ----------
  def _fmt_date(self, d):
    try:
      if isinstance(d, (datetime, date)):
        return d.strftime("%Y-%m-%d")
      if isinstance(d, str):
        return d.split("T")[0]
    except Exception:
      pass
    return "–"
  
  def _call(self, name, *args, **kwargs):
    resp = anvil.server.call(name, *args, **kwargs)
    if resp is None:
      raise RuntimeError(f"{name} returned no data")
    return resp

  def _set_editable(self, editable: bool):
    for w in (getattr(self, "drop_down_customer", None),
              getattr(self, "text_area_notes", None),
              getattr(self, "button_add_line", None)):
      if w is not None:
        w.enabled = editable
    # pass into rows
    items = list(self.repeating_panel_lines.items or [])
    for it in items:
      it["_editable"] = editable
    self.repeating_panel_lines.items = items

  def _refresh_ship_to(self, customer_id: str):
    try:
      if not customer_id:
        self.label_ship_to.text = ""
        self.label_customer_id.text = ""
        return
      ship_str = self._call("customer_default_shipping_address_string", customer_id) or ""
      self.label_ship_to.text = ship_str
      self.label_customer_id.text = customer_id
    except Exception as ex:
      print(f"ship_to load failed: {ex}")
      self.label_ship_to.text = ""


  # ---------- load & bind ----------
  def _load(self):
    self.order = self._call("sales_order_get", self.order_id) or {}

    # Build dropdown: name -> business customer_id (needs server to return it; see server patch below)
    choices = self._call("customer_list_choices") or []  # [{"customer_id","customer_name"}]
    self._cust_map = {c.get("customer_name",""): c.get("customer_id","") for c in choices}
    self.drop_down_customer.items = list(self._cust_map.keys())

    # Header
    self.label_so_id.text = self.order.get("_id","")
    self.label_status.text = (self.order.get("status","") or "").upper()
    self.label_order_date.text = self._fmt_date(self.order.get("order_date"))

    cur_name = self.order.get("customer_name") or ""
    self.drop_down_customer.selected_value = cur_name if cur_name in self._cust_map else None
    self.label_customer_id.text = self._cust_map.get(cur_name, self.order.get("customer_id",""))
    self._refresh_ship_to(self.label_customer_id.text)

    self.text_area_notes.text = self.order.get("notes","")

    # Lines
    is_draft = ((self.order.get("status") or "").strip().lower() == "draft")
    lines = list(self.order.get("lines", []) or [])
    for ln in lines:
      ln["_editable"] = is_draft
    self.repeating_panel_lines.items = lines

    # Totals
    a = self.order.get("amounts", {}) or {}
    self.label_subtotal.text = f"{float(a.get('subtotal', 0.0) or 0.0):.2f}"
    self.label_tax.text      = f"{float(a.get('tax', 0.0) or 0.0):.2f}"
    self.label_shipping.text = f"{float(a.get('shipping', 0.0) or 0.0):.2f}"
    self.label_grand.text    = f"{float(a.get('grand_total', 0.0) or 0.0):.2f}"

    self._set_editable(is_draft)

  # ---------- header events ----------
  def drop_down_customer_change(self, **e):
    name = self.drop_down_customer.selected_value or ""
    cust_id = self._cust_map.get(name, "")
    self.label_customer_id.text = cust_id
    self._refresh_ship_to(cust_id)
  
    if name and cust_id:
      try:
        self._call("sales_order_update", self.order_id, {"customer_name": name, "customer_id": cust_id})
        self._load()  # reload to show any re-priced taxes/totals
      except Exception as ex:
        Notification(f"Failed to set customer: {ex}", style="warning").show()


  def _save_header(self):
    payload = {"notes": self.text_area_notes.text or ""}
    name = self.drop_down_customer.selected_value or ""
    cust_id = self._cust_map.get(name, "")
    if name and cust_id:
      payload["customer_name"] = name
      payload["customer_id"] = cust_id
    self.order = self._call("sales_order_update", self.order_id, payload)

  def button_save_click(self, **e):
    try:
      self._save_header()
      self._persist_all_rows()
      self._load()
      Notification("Saved.", style="success").show()
    except Exception as ex:
      Notification(f"Save failed: {ex}", style="warning").show()

  def button_confirm_click(self, **e):
    try:
      self._persist_all_rows()
      self.order = self._call("sales_order_confirm", self.order_id)
      self._load()
      Notification("Order confirmed.", style="success").show()
    except Exception as ex:
      Notification(f"Confirm failed: {ex}", style="warning").show()

  def button_cancel_click(self, **e):
    try:
      self.order = self._call("sales_order_cancel", self.order_id)
      self._load()
      Notification("Order cancelled.", style="success").show()
    except Exception as ex:
      Notification(f"Cancel failed: {ex}", style="warning").show()

  def button_back_click(self, **e):
    open_form("SalesOrderRecords")

  # ---------- lines ----------
  def button_add_line_click(self, **e):
    items = list(self.repeating_panel_lines.items or [])
    next_line_no = (max([int(x.get("line_no", 0) or 0) for x in items], default=0) + 1)
    is_draft = ((self.order.get("status") or "").strip().lower() == "draft")
    items.insert(0, {
      # no _id yet (it's created by server on first add)
      "line_no": next_line_no,
      "part_id": "",
      "description": "",
      "uom": "ea",
      "unit_price": 0.0,
      "qty_ordered": 0.0,
      "line_price": 0.0,
      "line_tax": 0.0,
      "_editable": is_draft
    })
    self.repeating_panel_lines.items = items

  # ---------- work orders ----------
  def button_create_wos_click(self, **event_args):
    if not self._preflight_missing_routes_or_block():
      return
    so_id = (self.label_so_id.text or "").strip()  # however you store it
    if not so_id:
      alert("No Sales Order open.")
      return
    try:
      result = anvil.server.call("so_plan_to_wos_debug", so_id)  # <- debug version
      created = len(result.get("created", []))
      updated = len(result.get("updated", []))
      skipped = len(result.get("skipped", []))
      notes   = result.get("notes", [])
      logs    = result.get("logs", [])
      Notification(f"WOs → created:{created}, updated:{updated}, skipped:{skipped}", style="success").show()
      if notes:
        alert("\n".join(notes))
      # Optional: show logs in a scrollable alert for now
      if logs:
        alert(TextArea(text="\n".join(logs), height=300, width=700, enabled=False))
    except Exception as ex:
      alert(f"WO planning failed: {ex}")

  def button_view_work_orders_click(self, **event_args):
    so_id = (self.label_so_id.text or "").strip()
    if not so_id:
      alert("No Sales Order open."); return
    try:
      open_form("WorkOrderRecords", filter_sales_order_id=so_id)
    except Exception:
      open_form("WorkOrderRecords")

  
  def _delete_so_line(self, row_index=None, line_id=None, **e):
    try:
      items = list(self.repeating_panel_lines.items or [])
      if line_id:
        self._call("sales_order_delete_line", line_id)
        self._load()
        Notification("Line deleted.", style="success").show()
        return
  
      # No _id yet → it was never persisted; just remove from the panel
      if 0 <= (row_index or -1) < len(items):
        del items[row_index]
        self.repeating_panel_lines.items = items
  
    except Exception as ex:
      Notification(f"Delete failed: {ex}", style="warning").show()

  def _persist_all_rows(self):
    items = list(self.repeating_panel_lines.items or [])
    for it in items:
      if not it.get("_editable"):
        continue
      part_id = (it.get("part_id") or "").strip()
      try:
        qty = float(it.get("qty_ordered") or 0)
      except Exception:
        qty = 0.0
      if not part_id or qty <= 0:
        continue
  
      if it.get("_id"):
        self._call("sales_order_update_line", it["_id"], {"qty_ordered": qty})
      else:
        new_line = self._call("sales_order_add_line", self.order_id, {"part_id": part_id, "qty_ordered": qty})
        it["_id"] = new_line.get("_id")   # keep it from disappearing
    # Optional: write back updated items so rows remember _id without waiting for reload
    self.repeating_panel_lines.items = items

  def _refresh_so_line(self, row_index, part_id, qty_ordered, line_no=None, line_id=None, **e):
    try:
      items = list(self.repeating_panel_lines.items or [])
      if not (0 <= row_index < len(items)):
        return
  
      if line_id:
        updated_line = self._call("sales_order_update_line", line_id, {"qty_ordered": float(qty_ordered or 0)})
      else:
        updated_line = self._call("sales_order_add_line", self.order_id, {
          "part_id": (part_id or "").strip(),
          "qty_ordered": float(qty_ordered or 0),
        })
  
      # Replace only this row with authoritative server values (unit_price, line_price, line_tax)
      row = dict(items[row_index])
      editable = row.get("_editable", False)
      line_no_fallback = row.get("line_no")
      row.update(updated_line or {})
      row["_editable"] = editable
      if line_no_fallback is not None and row.get("line_no") in [None, ""]:
        row["line_no"] = line_no_fallback
      items[row_index] = row
      self.repeating_panel_lines.items = items
  
      # Refresh header totals (amounts)
      self.order = self._call("sales_order_get", self.order_id) or {}
      a = self.order.get("amounts", {}) or {}
      self.label_subtotal.text = f"{float(a.get('subtotal', 0.0) or 0.0):.2f}"
      self.label_tax.text      = f"{float(a.get('tax', 0.0) or 0.0):.2f}"
      self.label_shipping.text = f"{float(a.get('shipping', 0.0) or 0.0):.2f}"
      self.label_grand.text    = f"{float(a.get('grand_total', 0.0) or 0.0):.2f}"
  
    except Exception as ex:
      Notification(f"Update line failed: {ex}", style="warning").show()











