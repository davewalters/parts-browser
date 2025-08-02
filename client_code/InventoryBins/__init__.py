from ._anvil_designer import InventoryBinsTemplate
from anvil import *
import anvil.server

class InventoryBins(InventoryBinsTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.repeating_panel_bins.role = "scrolling-panel"

    self.text_box_filter_part_id.set_event_handler("change", self.update_filter)
    self.text_box_filter_part_name.set_event_handler("change", self.update_filter)

    self.update_filter()

  def update_filter(self, **event_args):
    part_id = self.text_box_filter_part_id.text or ""
    part_name = self.text_box_filter_part_name.text or ""

    try:
      bins = anvil.server.call("get_filtered_inventory_bins", part_id, part_name)
      self.repeating_panel_bins.items = bins
      self.label_count.text = f"{len(bins)} bins returned"
    except Exception as e:
      self.label_count.text = f"Error: {e}"
      self.repeating_panel_bins.items = []

  def button_add_bin_click(self, **event_args):
    # Append a placeholder row with no _id to trigger auto ID generation
    new_row = {
      "_id": "",
      "part_id": "",
      "part_name": "",
      "qty": 0,
      "owner": "Manufacturing",
      "serial_numbers": []
    }
    self.repeating_panel_bins.items = self.repeating_panel_bins.items + [new_row]

  def button_home_click(self, **event_args):
    open_form("Nav")

