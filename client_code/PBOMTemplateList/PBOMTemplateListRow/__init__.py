from ._anvil_designer import PBOMTemplateListRowTemplate
from anvil import *

class PBOMTemplateListRow(PBOMTemplateListRowTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)
    # For debugging: proves rows are created
    print("PBOMTemplateListRow __init__")

    # Bind labels directly to item fields (no event hooks required)
    self.label_id.data_bindings = [{"property": "text", "code": "(self.item or {}).get('display_id') or ''"}]
    self.label_parent_id.data_bindings = [{"property": "text", "code": "(self.item or {}).get('parent_part_id') or ''"}]
    self.label_parent_desc.data_bindings = [{"property": "text", "code": "(self.item or {}).get('parent_desc') or ''"}]
    self.label_rev.data_bindings = [{"property": "text", "code": "(self.item or {}).get('rev') or ''"}]
    self.label_plant.data_bindings = [{"property": "text", "code": "(self.item or {}).get('plant_id') or ''"}]
    self.label_variant.data_bindings = [{"property": "text", "code": "(self.item or {}).get('variant') or ''"}]
    self.label_status.data_bindings = [{"property": "text", "code": "(self.item or {}).get('status') or ''"}]

  def button_select_click(self, **event_args):
    # Bubble up to the list to handle navigation
    self.parent.raise_event("x-open-detail", row=self.item)






