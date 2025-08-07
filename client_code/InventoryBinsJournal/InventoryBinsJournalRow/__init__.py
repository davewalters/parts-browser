from ._anvil_designer import InventoryBinsJournalRowTemplate
from anvil import *

class InventoryBinsJournalRow(InventoryBinsJournalRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.update_display()

  def update_display(self):
    self.label_timestamp.text = self.item["formatted_timestamp"]
    self.label_part_id.text = self.item["part_id"]
    self.label_location.text = self.item.get("location", "")
    self.label_bin_id.text = self.item.get("bin_id", "")
    self.label_owner.text = self.item.get("owner", "")

    qty = self.item.get("qty", 0)
    self.label_qty.text = f"{qty:+d}" if qty != 0 else "0"
    self.label_qty.foreground = "secondary500" if qty > 0 else "primary500" if qty < 0 else None

    balance = self.item.get("running_balance", 0)
    self.label_running_balance.text = f"{balance:.2f}"
    self.label_running_balance.foreground = (
      "secondary500" if balance > 0 else
      "primary500" if balance < 0 else None
    )

