from ._anvil_designer import InventoryStatusRowTemplate
from anvil import *

class InventoryStatusRow(InventoryStatusRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.display_fields()

  def display_fields(self):
    self.label_timestamp.text = self.item.get("formatted_timestamp", "")
    self.label_part_id.text = self.item.get("part_id", "")

    # Show deltas using colored labels
    self.set_label_value(self.label_on_order, self.item.get("qty_on_order", 0))
    self.set_label_value(self.label_on_hand, self.item.get("qty_on_hand", 0))
    self.set_label_value(self.label_committed, self.item.get("qty_committed", 0))
    self.set_label_value(self.label_picked, self.item.get("qty_picked", 0))
    self.set_label_value(self.label_issued, self.item.get("qty_issued", 0))
    

    # Show running balance (already formatted by server)
    self.label_running_balance.text = self.item.get("formatted_balance", "")
    running_value = self.item.get("running_balance", 0)
    self.label_running_balance.foreground = (
      "secondary500" if running_value > 0 else
      "primary500" if running_value < 0 else None
    )

  def set_label_value(self, label, value):
    if value is None:
      label.text = "0"
      label.foreground = None
    else:
      label.text = f"{value:d}" if isinstance(value, int) else f"{value:.2f}"
      label.foreground = (
        "#03A9F4" if value > 0 else
        "#FF9800" if value < 0 else
        None
      )



