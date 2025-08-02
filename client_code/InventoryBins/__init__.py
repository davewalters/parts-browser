from ._anvil_designer import InventoryBinsTemplate
from anvil import *
import anvil.server

class InventoryBins(InventoryBinsTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)
    self.button_home.role = "mydefault-button"
    self.button_add_bin.role = "new-button"
    self.repeating_panel_bins.role = "scrolling-panel"

    self.load_bins()

  def load_bins(self):
    self.rows = anvil.server.call("get_inventory_bins_full")
    self.repeating_panel_bins.items = self.rows
    self.label_count.text = f"{len(self.rows)} bins"

  def button_add_bin_click(self, **event_args):
    new_bin = {
      "_id": "",
      "owner": "Manufacturing",
      "location": "",
      "serial_numbers": [],
      "part_id": None,
      "created": None
    }
    self.rows.append(new_bin)
    self.repeating_panel_bins.items = list(self.rows)  # force UI refresh

  def button_home_click(self, **event_args):
    open_form("Nav")

