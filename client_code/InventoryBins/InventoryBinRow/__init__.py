from ._anvil_designer import InventoryBinRowTemplate
from anvil import *

class InventoryBinRow(InventoryBinRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_save.role = "save-button"
    self.button_delete.role = "delete-button"
    self.drop_down_owner.items = ["Manufacturing", "Stores", "Shipping", "WIP", "QA"]

    if self.item:
      self.text_box_id.text = self.item.get("_id", "")
      self.label_part_id.text = self.item.get("part_id", "")
      self.label_part_name.text = self.item.get("part_name", "")
      self.label_qty.text = str(self.item.get("qty", 0))
      self.drop_down_owner.selected_value = self.item.get("owner", "Manufacturing")
      self.text_box_location.text = self.item.get("location", "")

      serials = self.item.get("serial_numbers", [])
      self.text_area_serials.text = "\n".join(serials)
      self.check_box_lot_traced.checked = bool(serials)
      self.check_box_lot_traced.enabled = False

