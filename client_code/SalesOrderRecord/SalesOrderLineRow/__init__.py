from ._anvil_designer import SalesOrderLineRowTemplate
from anvil import *

class SalesOrderLineRow(SalesOrderLineRowTemplate):
  def __init__(self, **props):
    self.init_components(**props)
    self._bind()

  def _fmt(self, x):
    try:
      return f"{float(x or 0.0):.2f}"
    except Exception:
      return "0.00"

  def _bind(self):
    it = self.item or {}
    editable = bool(it.get("_editable", False))
  
    # Editable fields
    self.text_box_part_id.text = it.get("part_id", "")
    self.text_box_qty_ordered.text = (
      "" if it.get("qty_ordered") in [None, ""] else str(it.get("qty_ordered"))
    )
    self.text_box_part_id.enabled = editable
    self.text_box_qty_ordered.enabled = editable
  
    # Read-only labels
    self.label_line_no.text     = str(it.get("line_no", ""))
    self.label_desc.text        = it.get("description", "")
    self.label_uom.text         = it.get("uom", "ea")
    self.label_unit_price.text  = self._fmt(it.get("unit_price", 0))
    self.label_line_price.text = self._fmt(it.get("line_price", 0))
    
    #if hasattr(self, "label_line_price"):
    #  try:
    #    qty = float(it.get("qty_ordered") or 0)
    #    unit = float(it.get("unit_price") or 0)
    #    line_price = it.get("line_price")
    #    if line_price is None:
    #      line_price = qty * unit
    #  except Exception:
    #    line_price = 0.0
    #  self.label_line_price.text = self._fmt(line_price)

    self.label_line_tax.text    = self._fmt(it.get("line_tax", 0))

    line_total = it.get("line_total")
    if line_total is None:
      try:
        lp = float(it.get("line_price") or 0)
        t = float(it.get("line_tax") or 0)
        line_total = lp + t
      except Exception:
        line_total = 0.0
    if hasattr(self, "label_line_total"):
      self.label_line_total.text = self._fmt(line_total)
  
    if hasattr(self, "button_delete"):
      self.button_delete.enabled = editable


  # ----- utilities -----
  def _panel(self):
    p = self.parent
    while p:
      if hasattr(p, "items"):
        return p
      p = p.parent
    return None

  def _sync_item_from_ui(self):
    """Write current edits back to self.item so the parent sees them."""
    it = self.item or {}
    it["part_id"] = (self.text_box_part_id.text or "").strip()
    try:
      it["qty_ordered"] = float(self.text_box_qty_ordered.text or "0")
    except Exception:
      it["qty_ordered"] = 0.0
    self.item = it  # rebind row’s item

  def _raise_refresh(self):
    panel = self._panel()
    if not panel or self.item not in (panel.items or []):
      return
    self._sync_item_from_ui()  # <— IMPORTANT
    row_index = panel.items.index(self.item)
    panel.raise_event(
      "x-refresh-so-line",
      row_index=row_index,
      part_id=self.item.get("part_id", ""),
      qty_ordered=self.item.get("qty_ordered", 0.0),
      line_no=self.item.get("line_no"),
      line_id=self.item.get("_id")  # may be None for new rows
    )

  # ----- events: both blur and enter -----
  def text_box_part_id_lost_focus(self, **e):
    self._raise_refresh()

  def text_box_qty_ordered_lost_focus(self, **e):
    self._raise_refresh()

  def text_box_part_id_pressed_enter(self, **e):
    self._raise_refresh()

  def text_box_qty_ordered_pressed_enter(self, **e):
    self._raise_refresh()

  def button_delete_click(self, **e):
    panel = self._panel()
    if not panel:
      return
    if confirm("Delete this line?"):
      self._sync_item_from_ui()
      row_index = (panel.items or []).index(self.item)
      panel.raise_event("x-delete-so-line", row_index=row_index, line_id=self.item.get("_id"))







