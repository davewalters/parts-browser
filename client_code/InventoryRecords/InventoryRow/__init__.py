from ._anvil_designer import InventoryRowTemplate
from anvil import *

class InventoryRow(InventoryRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_view.set_event_handler("click", self.view_button_click)

    self.label_part_id.text = self.item['part']['_id']
    self.label_part_name.text = self.item['part']['name']
    self.label_bin.text = self.item['bin']
    self.label_owner.text = self.item['owner']
    self.label_kanban.text = "Yes" if self.item.get('is_kanban') else "No"

    self.label_on_hand.text = str(self.item.get('qty_on_hand', 0))
    self.label_committed.text = str(self.item.get('qty_committed', 0))
    self.label_staged.text = str(self.item.get('qty_staged', 0))
    self.label_issued.text = str(self.item.get('qty_issued', 0))
    self.label_on_order.text = str(self.item.get('qty_on_order', 0))

  def view_button_click(self, **event_args):
    self.raise_event("x-show-detail", inventory_row=self.item)

