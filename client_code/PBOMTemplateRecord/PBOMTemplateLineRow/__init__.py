from ._anvil_designer import PBOMTemplateLineRowTemplate
from anvil import *

class PBOMTemplateLineRow(PBOMTemplateLineRowTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)

    # Clear designer bindings
    for w in [
      self.label_line_no, self.label_part_id, self.label_desc,
      self.label_qty_per, self.label_unit, self.label_lot_traced,
      self.label_serial_required, self.label_cut_info
    ]:
      try: w.data_bindings = []
      except Exception: pass

    # Data-bind simple fields
    self.label_line_no.data_bindings        = [{"property":"text","code":"(self.item or {}).get('_row_no','')"}]
    self.label_part_id.data_bindings        = [{"property":"text","code":"(self.item or {}).get('part_id','')"}]
    self.label_desc.data_bindings           = [{"property":"text","code":"(self.item or {}).get('desc','')"}]
    self.label_qty_per.data_bindings        = [{"property":"text","code":"f\"{float((self.item or {}).get('qty_per',0) or 0):g}\""}]
    self.label_unit.data_bindings           = [{"property":"text","code":"(self.item or {}).get('unit','')"}]
    self.label_lot_traced.data_bindings     = [{"property":"text","code":"'Yes' if (self.item or {}).get('lot_traced') else 'No'"}]
    self.label_serial_required.data_bindings= [{"property":"text","code":"'Yes' if (self.item or {}).get('serial_required') else 'No'"}]

    # Cut info in base units: “Cut 11 mm”
    self.label_cut_info.data_bindings = [
      {"property":"visible","code":"bool(((self.item or {}).get('cut') or {}).get('base_unit'))"},
      {"property":"text","code":
       "lambda i=(self.item or {}): (lambda c=i.get('cut') or {}: "
       "  f\"Cut {float(c.get('base_value',0) or 0):g} {c.get('base_unit','')}\" if c.get('base_unit') else ''"
       ")()"
      }
    ]






  

