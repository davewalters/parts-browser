from ._anvil_designer import PBOMTemplateLineRowTemplate
from anvil import *

class PBOMTemplateLineRow(PBOMTemplateLineRowTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)

    # (Optional) clear any designer bindings to avoid duplicates
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

    # Simple, readable data bindings
    self.label_part_id.data_bindings         = [{"property": "text", "code": "(self.item or {}).get('part_id','')"}]
    self.label_desc.data_bindings            = [{"property": "text", "code": "(self.item or {}).get('desc','')"}]
    self.label_qty_per.data_bindings         = [{"property": "text", "code": "f\"{(self.item or {}).get('qty_per',0):g}\""}]
    self.label_unit.data_bindings            = [{"property": "text", "code": "(self.item or {}).get('unit','')"}]
    self.label_lot_traced.data_bindings      = [{"property": "text", "code": "\"Yes\" if (self.item or {}).get('lot_traced') else \"No\""}]
    self.label_serial_required.data_bindings = [{"property": "text", "code": "\"Yes\" if (self.item or {}).get('serial_required') else \"No\""}]

    # Optional “cut:” hint (only if you've added label_cut_info in the designer)
    try:
      self.label_cut_info.data_bindings = [
        {"property": "visible", "code": "bool((self.item or {}).get('cut'))"},
        {"property": "text", "code":
         "lambda i=(self.item or {}): "
         " (lambda c=i.get('cut') or {}: "
         "   f\"cut: {c.get('base_value',0):g} {c.get('base_unit','')}\" "
         " )()"
        }
      ]
    except Exception:
      pass

  def set_item(self, item):
    # keep default binding behaviour
    self.item = item or {}

    # minimal, robust line number compute (works even with DataRowPanel nesting)
    try:
      rp = self.parent  # the template's parent is the RP
      items = list(getattr(rp, "items", []) or [])
      idx = items.index(self.item) if self.item in items else -1
      self.label_line_no.text = str(idx + 1) if idx >= 0 else ""
    except Exception:
      self.label_line_no.text = ""


  

