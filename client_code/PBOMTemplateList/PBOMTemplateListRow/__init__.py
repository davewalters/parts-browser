from ._anvil_designer import PBOMTemplateListRowTemplate
from anvil import *

class PBOMTemplateListRow(PBOMTemplateListRowTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)

  def form_show(self, **event_args):
    i = self.item or {}
    self.label_id.text          = i.get("_id", "")
    self.label_parent_id.text   = i.get("parent_part_id", "")
    self.label_parent_desc.text = i.get("parent_desc", "") or ""
    self.label_rev.text         = i.get("rev", "") or ""
    self.label_plant.text       = i.get("plant_id", "") or ""
    self.label_variant.text     = i.get("variant", "") or ""
    self.label_status.text      = i.get("status", "") or ""

  def button_select_click(self, **event_args):
    # Bubble up to the list to handle navigation
    self.parent.raise_event("x-open-detail", row=self.item)


