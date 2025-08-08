from ._anvil_designer import InventoryRowTemplate
from anvil import *

class InventoryRow(InventoryRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

    self.label_part_id.text = self.item['part_id']
    self.label_part_name.text = self.item['part_name']
    self.label_kanban.text = "Yes" if self.item.get('is_kanban') else "No"

    self.label_on_hand.text = str(self.item.get('qty_on_hand', 0))
    self.label_committed.text = str(self.item.get('qty_committed', 0))
    self.label_picked.text = str(self.item.get('qty_picked', 0))
    self.label_issued.text = str(self.item.get('qty_issued', 0))
    self.label_on_order.text = str(self.item.get('qty_on_order', 0))

    self.button_status_transfers.set_event_handler("click", self.button_status_transfers_click)
    self.button_bin_transfers.set_event_handler("click", self.button_bin_transfers_click)

  def button_status_transfers_click(self, **event_args):
    self.parent.raise_event("x-status_transfer", part_summary=self.item)

  def button_bin_transfers_click(self, **event_args):
    self.parent.raise_event("x-bin_transfer", part_summary=self.item)