from ._anvil_designer import InventoryBinRowTemplate
from anvil import *
import anvil.server

class InventoryBinRow(InventoryBinRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

    self.text_box_bin_id.set_event_handler("change", self.save_changes)
    self.text_box_qty.set_event_handler("change", self.save_changes)
    self.drop_down_owner.set_event_handler("change", self.save_changes)
    self.drop_down_location.set_event_handler("change", self.save_changes)
    self.text_area_serials.set_event_handler("change", self.save_changes)
    self.button_delete.set_event_handler("click", self.delete_bin)

    self.drop_down_owner.items = ["Manufacturing", "Warehouse"]
    self.drop_down_location.items = ["STORE", "WIP", "FINISHEDGOODS"]
    self.refresh_ui()

  def refresh_ui(self):
    self.text_box_bin_id.text = self.item.get("_id", "")
    self.label_part_id.text = self.item.get("part_id", "")
    self.label_part_name.text = self.item.get("part_name", "")
    self.text_box_qty.text = str(self.item.get("qty", 0))
    self.drop_down_owner.selected_value = self.item.get("owner", "Manufacturing")
    self.drop_down_location.selected_value = self.item.get("location", "Store")
    self.text_area_serials.text = "\n".join(self.item.get("serial_numbers", []))

  def save_changes(self, **event_args):
    self.item["_id"] = self.text_box_bin_id.text.strip()
    self.item["part_id"] = self.label_part_id.text.strip()
    self.item["part_name"] = self.label_part_name.text.strip()
    self.item["qty"] = int(self.text_box_qty.text or 0)
    self.item["owner"] = self.drop_down_owner.selected_value
    self.item["location"] = self.drop_down_location.selected_value
    self.item["serial_numbers"] = [s.strip() for s in self.text_area_serials.text.split("\n") if s.strip()]

    try:
      anvil.server.call("save_inventory_bin", self.item)
    except Exception as e:
      alert(f"Error saving bin: {e}")

  def delete_bin(self, **event_args):
    bin_id = self.item.get("_id")
    if bin_id:
      confirmed = confirm(f"Are you sure you want to delete bin '{bin_id}'?")
      if confirmed:
        try:
          anvil.server.call("delete_inventory_bin", bin_id)
          self.parent.raise_event("x-refresh")
        except Exception as e:
          alert(f"Cannot delete bin: {e}")

