from anvil import *
from ._anvil_designer import ItemTemplate1Template
from datetime import datetime

class ItemTemplate1(ItemTemplate1Template):
  def __init__(self, **properties):    
    self.init_components(**properties)
    cost_info = self.item.get("latest_cost", {})
    self.label_id.text = self.item['_id']
    self.label_rev.text = self.item.get('revision', '')
    self.label_desc.text = self.item.get('description', '')
    self.label_status.text = self.item.get('status', '')
    self.label_vendor.text = self.item.get('default_vendor', '')
    self.label_cost_nz.text = f"${cost_info.get('cost_nz'):.2f}" if cost_info.get("cost_nz") else "-"
    
    raw_date = cost_info.get("cost_date")
    if raw_date:
      try:
        dt = datetime.fromisoformat(raw_date)
        self.label_cost_date.text = dt.strftime("%d/%m/%Y")  # or use %Y-%m-%d if preferred
      except Exception:
        self.label_cost_date.text = raw_date  # fallback if parsing fails
    else:
      self.label_cost_date.text = "-"



  def button_view_click(self, **event_args):
    print("👀 button_view clicked")
    self.parent.raise_event("x-show-detail", part=self.item)


