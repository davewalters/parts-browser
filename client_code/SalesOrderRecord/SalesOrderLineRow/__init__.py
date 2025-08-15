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

    # Editable text boxes
    self.text_box_part_id.text = it.get("part_id","")
    self.text_box_qty_ordered.text = (
      "" if it.get("qty_ordered") in [None, ""] else str(it.get("qty_ordered"))
    )
    self.text_box_part_id.enabled = editable
    self.text_box_qty_ordered.enabled = editable

    # Read-only labels
    self.label_line_no.text     = str(it.get("line_no",""))
    self.label_desc.text        = it.get("description","")
    self.label_uom.text         = it.get("uom","ea")
    self.label_unit_price.text  = self._fmt(it.get("unit_price",0))
    self.label_line_tax.text    = self._fmt(it.get("line_tax",0))

    # line total (qty * price) if server didn’t send one
    line_total = it.get("line_total")
    if line_total is None:
      try:
        q = float(it.get("qty_ordered") or 0)
        p = float(it.get("unit_price") or 0)
        line_total = q * p
      except Exception:
        line_total = 0.0
    if hasattr(self, "label_line_total"):
      self.label_line_total.text = self._fmt(line_total)

    # Delete button only in draft
    if hasattr(self, "button_delete"):
      self.button_delete.enabled = editable

  # ----- helpers -----
  def _raise_refresh(self):
    panel = self._get_panel()
    if not panel or self.item not in (panel.items or []):
      return
    row_index = panel.items.index(self.item)
    part_id = (self.text_box_part_id.text or "").strip()
    try:
      qty = float(self.text_box_qty_ordered.text or "0")
    except Exception:
      qty = 0.0
    line_no = self.item.get("line_no")
    panel.raise_event("x-refresh-so-line",
                      row_index=row_index,
                      part_id=part_id,
                      qty_ordered=qty,
                      line_no=line_no)

  def _get_panel(self):
    p = self.parent
    while p:
      if hasattr(p, "items"):
        return p
      p = p.parent
    return None

  # ----- events -----
  def text_box_part_id_lost_focus(self, **e):
    self._raise_refresh()

  def text_box_qty_ordered_lost_focus(self, **e):
    self._raise_refresh()

  def text_box_qty_ordered_pressed_enter(self, **e):
    self._raise_refresh()

  def button_delete_click(self, **e):
    panel = self._get_panel()
    if not panel:
      return
    if confirm("Delete this line?"):
      line_no = self.item.get("line_no")
      row_index = panel.items.index(self.item)
      panel.raise_event("x-delete-so-line", row_index=row_index, line_no=line_no)




