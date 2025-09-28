# client_code/ShortageRecordsRow/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import ShortageRecordsRowTemplate

class ShortageRecordsRow(ShortageRecordsRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_create_order.role = "save-button"
    self.check_box_select.set_event_handler('change', self._on_select_change)

  def form_show(self, **event_args):
    d = dict(self.item or {})
    self.label_part_id.text    = d.get("part_id","")
    self.label_desc.text       = d.get("part_desc","")
    self.label_unit.text       = d.get("unit","")
    # Display both for context
    self.label_open_qty.text   = str(d.get("open_short_qty", 0))
    self.label_total_qty.text  = str(d.get("total_short_qty", 0))
    self.label_vendor.text     = d.get("default_vendor_name","") or ""
    self.label_suggestion.text = d.get("suggestion","")
    self.label_status.text     = d.get("status","open")

    # DEFAULT ACTION QTY = OPEN (orderable) qty
    open_q = d.get("open_short_qty", 0)
    self.text_action_qty.text = str(open_q)

    # reflect parent’s selection state
    self.check_box_select.checked = bool(d.get("_selected", False))

  def _on_select_change(self, **e):
    sid = (self.item or {}).get("_id")
    self.parent.raise_event("x-select-changed", shortage_id=sid, checked=bool(self.check_box_select.checked))

  def button_create_order_click(self, **event_args):
    d = dict(self.item or {})
    sid = d.get("_id")
    if not sid:
      alert("Missing shortage id."); return

    # If the operator leaves it blank, fall back to open qty
    qty_s = (self.text_action_qty.text or "").strip()
    if qty_s == "":
      qty_s = str(d.get("open_short_qty", 0))

    try:
      qty = float(qty_s)
      if qty <= 0:
        alert("Quantity must be > 0."); return
    except Exception:
      alert("Invalid quantity."); return

    # Optional due date for make→WO
    due = None
    try:
      if hasattr(self.date_due, "date") and self.date_due.date:
        due = self.date_due.date
    except Exception:
      pass

    try:
      res = anvil.server.call("shortage_act", sid, qty, due)
      if res and res.get("ok"):
        msg = f"Created {res.get('action').upper()}: {res.get('wo_id') or res.get('po_id')}"
        Notification(msg, style="success").show()
        self.parent.raise_event("x-refresh")
      else:
        alert(f"Action failed: {res}")
    except Exception as ex:
      alert(f"Action failed: {ex}")


