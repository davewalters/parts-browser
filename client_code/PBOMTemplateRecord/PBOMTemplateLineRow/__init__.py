from anvil import *

class PBOMTemplateLineRow(PBOMTemplateLineRowTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)

  def form_show(self, **e):
    # Compute line number from current items
    items = list(self.parent.items or [])
    index = items.index(self.item) if self.item in items else 0
    self.label_line_no.text = str(index + 1)

    # Bind read-only labels
    i = self.item or {}
    self.label_part_id.text        = i.get("part_id", "")
    self.label_desc.text           = i.get("desc", "") or ""
    self.label_qty_per.text        = f'{(i.get("qty_per") or 0):g}'
    self.label_unit.text           = i.get("unit", "") or ""
    self.label_lot_traced.text     = "Yes" if i.get("lot_traced") else "No"
    self.label_serial_required.text= "Yes" if i.get("serial_required") else "No"

  

