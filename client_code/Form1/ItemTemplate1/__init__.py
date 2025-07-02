from anvil import *
from ._anvil_designer import ItemTemplate1Template

class ItemTemplate1(ItemTemplate1Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.label_id.text = self.item['_id']
    self.label_rev.text = self.item.get('revision', '')
    self.label_desc.text = self.item.get('description', '')
    self.label_status.text = self.item.get('status', '')
    self.label_vendor.text = self.item.get('default_vendor', '')


  def button_view_click(self, **event_args):
    self.parent.raise_event("x-show-detail", part=self.item)