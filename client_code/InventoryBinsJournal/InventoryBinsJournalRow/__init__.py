# client code: InventoryBinsJournalRow
from ._anvil_designer import InventoryBinsJournalRowTemplate
from anvil import *

class InventoryBinsJournalRow(InventoryBinsJournalRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.display_fields()

  def display_fields(self):
    self.label_timestamp.text = self.item.get("formatted_timestamp", "")
    self.label_part_id.text = self.item.get("part_id", "")
    self.label_part_name.text = self.item.get("part_name", "")
    
    self.label_source_bin_id.text = self.item.get("source_bin_id", "")
    source_bin_qty = self.item.get("running_balance_source", None)
    self.label_source_bin_qty.text = self._format_balance(source_bin_qty)
    
    self.label_target_bin_id.text = self.item.get("target_bin_id", "")
    target_bin_qty = self.item.get("running_balance_target", None)
    self.label_target_bin_qty.text = self._format_balance(target_bin_qty)

    transfer_qty = self.item.get("qty", 0) or 0
    self.label_transfer_qty.text = f"{transfer_qty:+.2f}" if isinstance(transfer_qty, (int, float)) else "0"
    self.label_transfer_qty.foreground = "#0D9488" if transfer_qty > 0 else ("#DC2626" if transfer_qty < 0 else None)

  def _format_balance(self, val):
    if val is None:
      return ""
    try:
      return f"{float(val):.2f}"
    except (TypeError, ValueError):
      return "0.00"


