from ._anvil_designer import InventoryBinTransferRowsTemplate
from anvil import *
import anvil.server


class InventoryBinTransferRows(InventoryBinTransferRowsTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.display_fields()

  def display_fields(self):
    self.label_bin_id.text = str(self.item.get("_id", ""))
    self.label_location.text = self.item.get("location", "")
    self.label_owner.text = self.item.get("owner", "")
    self.label_qty.text = str(self.item.get("qty", 0))
