from ._anvil_designer import PBOMTemplateLineRowTemplate
from anvil import *

class PBOMTemplateLineRow(PBOMTemplateLineRowTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)

    # Remove any designer data bindings that might conflict
    for w in [
      self.label_line_no,
      self.label_part_id,
      self.label_desc,
      self.label_qty_per,
      self.label_unit,
      self.label_lot_traced,
      self.label_serial_required,
    ]:
      try:
        w.data_bindings = []
      except Exception:
        pass

    # Initial render from the item provided at construction
    self._render(self.item or kwargs.get("item") or {})

  # RepeatingPanel calls this whenever the row's item is set/changed
  def set_item(self, item):
    self.item = item or {}
    self._render(self.item)

  def _render(self, i: dict):
    # Compute line number from the parent RepeatingPanel's items (robust even with DataRowPanel inside)
    try:
      rp = self.parent               # the row Form's parent is the RepeatingPanel
      items = list(rp.items or [])
      idx = items.index(self.item) if self.item in items else -1
      line_no = (idx + 1) if idx >= 0 else ""
    except Exception:
      line_no = ""
    self.label_line_no.text = str(line_no) if line_no != "" else ""

    # Bind read-only labels (with safe defaults)
    part_id = i.get("part_id") or ""
    desc    = i.get("desc") or ""
    qty     = i.get("qty_per")
    unit    = i.get("unit") or ""
    lot     = i.get("lot_traced") is True
    serial  = i.get("serial_required") is True

    # Format qty like your original (general format, no trailing zeros)
    try:
      qty_text = f"{float(qty):g}"
    except Exception:
      qty_text = "0"

    self.label_part_id.text         = part_id
    self.label_desc.text            = desc
    self.label_qty_per.text         = qty_text
    self.label_unit.text            = unit
    self.label_lot_traced.text      = "Yes" if lot else "No"
    self.label_serial_required.text = "Yes" if serial else "No"


  

