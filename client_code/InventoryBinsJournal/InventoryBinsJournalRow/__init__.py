from ._anvil_designer import InventoryBinsJournalRowTemplate
from anvil import *

class InventoryBinsJournalRow(InventoryBinsJournalRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.display_fields()

  def display_fields(self):
    item = self.item or {}
    self.label_timestamp.text = item.get("formatted_timestamp", "")
    self.label_part_id.text = item.get("part_id", "")
    self.label_part_name.text = item.get("part_name", "")
    self.label_source_bin_id.text = item.get("source_bin_id", "")
    self.label_target_bin_id.text = item.get("target_bin_id", "")

    # Show deltas as signed numbers; always show zeros if no change
    self.set_delta(self.label_source_bin_qty, item.get("src_delta", 0.0))
    self.set_delta(self.label_target_bin_qty, item.get("tgt_delta", 0.0))

  def set_delta(self, label, val):
    try:
      v = float(val or 0.0)
    except (TypeError, ValueError):
      v = 0.0
    label.text = f"{v:+.2f}"
    # Color: +ve blue, -ve orange, zero default
    label.foreground = (
      "#1976D2" if v > 0 else
      "#E65100" if v < 0 else
      None
    )



