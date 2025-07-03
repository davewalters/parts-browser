from anvil import *
from ._anvil_designer import ItemTemplate1Template

class ItemTemplate1(ItemTemplate1Template):
  def __init__(self, **properties):
    cost_info = self.item.get("latest_cost", {})
    
    self.init_components(**properties)
    self.label_id.text = self.item['_id']
    self.label_rev.text = self.item.get('revision', '')
    self.label_desc.text = self.item.get('description', '')
    self.label_status.text = self.item.get('status', '')
    self.label_vendor.text = self.item.get('default_vendor', '')
    self.label_cost_nz.text = f"${cost_info.get('cost_nz'):.2f}" if cost_info.get("cost_nz") else "-"
    self.label_cost_date.text = str(cost_info.get("cost_date") or "")


  def button_view_click(self, **event_args):
    self.parent.raise_event("x-show-detail", part=self.item)

