from anvil import *
import anvil.server
from ._anvil_designer import ItemTemplate1Template

class ItemTemplate1(ItemTemplate1Template):
  def __init__(self, **properties):
    self.init_components(**properties)

    # Extract fields from item
    part = self.item
    self.label_id.text = part.get("_id", "")
    self.label_rev.text = part.get("revision", "")
    self.label_desc.text = part.get("description", "")
    self.label_status.text = part.get("status", "")
    self.label_type.text = part.get("type", "")
    self.label_type.column = "type"
    self.label_vendor.text = part.get("default_vendor", "")

    cost_info = part.get("latest_cost", {})
    self.label_cost_nz.text = f"{cost_info.get('cost_nz', '')}" if cost_info else ""
    self.label_cost_date.text = f"{cost_info.get('cost_date', '')}" if cost_info else ""


  def button_view_click(self, **event_args):
    self.parent.raise_event("x-show-detail", part=self.item)


