from ._anvil_designer import PBOMTemplateLineRowTemplate
from anvil import *

class PBOMTemplateLineRow(PBOMTemplateLineRowTemplate):
  def __init__(self, **kwargs):
    # IMPORTANT: don't pass item into init_components; we render manually.
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

    # Initial render from the item provided at construction (if any)
    self._render(self.item or kwargs.get("item") or {})

  # RepeatingPanel calls this whenever the row's item is set/changed
  def set_item(self, item):
    self.item = item or {}
    self._render(self.item)

  def _render(self, i: dict):
    # Compute line number from the parent RepeatingPanel's items (robust even with DataRowPanel inside)
    try:
      rp = self.parent  # the row template's parent is the RepeatingPanel
      comps = list(rp.get_components())
      idx = comps.index(self)  # <-- index the component, not the dict item
      self.label_line_no.text = str(idx + 1)
    except Exception:
      self.label_line_no.text = ""

    # Bind read-only labels (with safe defaults)
    part_id = (i.get("part_id") or "").strip()
    desc    = i.get("desc") or ""
    qty     = i.get("qty_per")
    unit    = i.get("unit") or ""
    lot     = bool(i.get("lot_traced"))
    serial  = bool(i.get("serial_required"))

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

    # Optional: small “cut:” hint if you added a label_cut_info in the designer
    try:
      cut = i.get("cut") or {}
      if cut:
        # Operator-facing: reuse qty_per + unit (matches what they typed in the DesignBOM)
        self.label_cut_info.text = f"cut: {qty_text} {unit}"
        self.label_cut_info.visible = True
      else:
        self.label_cut_info.text = ""
        self.label_cut_info.visible = False
    except Exception:
      # If label_cut_info doesn't exist, just ignore
      pass




  

