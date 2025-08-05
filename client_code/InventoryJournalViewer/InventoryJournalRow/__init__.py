from ._anvil_designer import InventoryJournalRowTemplate
from anvil import *

class InventoryJournalRow(InventoryJournalRowTemplate):
  running_balance = None  # Shared class-level state

  def __init__(self, **properties):
    self.init_components(**properties)
    self.display_fields()

  def display_fields(self):
    self.label_timestamp.text = self.item["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    self.label_part_id.text = self.item["part_id"]
    #self.label_notes.text = self.item.get("notes", "")

    delta = self.item.get("delta", {})
    delta_on_hand = delta.get("qty_on_hand", 0)

    # Initialize running balance only once at top row
    if InventoryJournalRow.running_balance is None:
      InventoryJournalRow.running_balance = self.item.get("running_balance", delta_on_hand)
    else:
      InventoryJournalRow.running_balance -= delta_on_hand

    # Show deltas
    self.set_label_value(self.label_on_hand, delta_on_hand)
    self.set_label_value(self.label_committed, delta.get("qty_committed"))
    self.set_label_value(self.label_picked, delta.get("qty_picked"))
    self.set_label_value(self.label_issued, delta.get("qty_issued"))
    self.set_label_value(self.label_on_order, delta.get("qty_on_order"))

    # Show running balance (formatted like deltas)
    self.label_running_balance.text = f"{InventoryJournalRow.running_balance}"
    self.label_running_balance.foreground = (
      "secondary500" if InventoryJournalRow.running_balance > 0 else
      "primary500" if InventoryJournalRow.running_balance < 0 else None
    )

  def set_label_value(self, label, value):
    if value is None or value == 0:
      label.text = ""
      label.foreground = None
    else:
      label.text = f"{value:+}"
      label.foreground = "secondary500" if value > 0 else "primary500"

