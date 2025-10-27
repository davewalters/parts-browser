from ._anvil_designer import PBOMTemplateLineRowTemplate
from anvil import *

class PBOMTemplateLineRow(PBOMTemplateLineRowTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)

    # Nuke any designer bindings so nothing overwrites our text later
    for w in [
      self.label_line_no,
      self.label_part_id,
      self.label_desc,
      self.label_qty_per,
      self.label_unit,
      self.label_lot_traced,
      self.label_serial_required,
      getattr(self, "label_cut_info", None),
    ]:
      if w:
        try:
          w.data_bindings = []
        except Exception:
          pass

    # Initial render from provided item (if any)
    self._render(self.item or kwargs.get("item") or {})

  # RepeatingPanel will call this when the row item is set/changed
  def set_item(self, item):
    self.item = item or {}
    self._render(self.item)

  def _render(self, i: dict):
    # Safe accessors
    def _f(x, default=0.0):
      try:
        return float(x)
      except Exception:
        return float(default)

    # Line number (stamped by the parent form)
    row_no = i.get("_row_no")
    self.label_line_no.text = str(row_no) if row_no is not None else ""

    # Basic fields
    self.label_part_id.text  = i.get("part_id") or ""
    self.label_desc.text     = i.get("desc") or ""

    qty = _f(i.get("qty_per", 0))
    self.label_qty_per.text  = f"{qty:g}"
    self.label_unit.text     = i.get("unit") or ""
    self.label_lot_traced.text      = "Yes" if i.get("lot_traced") else "No"
    self.label_serial_required.text = "Yes" if i.get("serial_required") else "No"

    # Cut info (base units): "Cut 11 mm"
    cut_lbl = getattr(self, "label_cut_info", None)
    if cut_lbl:
      c = i.get("cut") or {}
      base_unit  = c.get("base_unit")
      base_value = _f(c.get("base_value", 0))
      if base_unit:
        cut_lbl.visible = True
        cut_lbl.text = f"Cut to: {base_value:g} {base_unit}"
      else:
        cut_lbl.visible = False
        cut_lbl.text = ""







  

