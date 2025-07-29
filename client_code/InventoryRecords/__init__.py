from anvil import *
import anvil.server
from anvil.js.window import setTimeout

from ._anvil_designer import InventoryRecordsTemplate
from .. import config

class InventoryRecords(InventoryRecordsTemplate):
  def __init__(self, 
               filter_part_id="",
               filter_part_name="", 
               filter_bin="", 
               filter_owner="", 
               filter_kanban=None,
               **kwargs):
    self.init_components(**kwargs)

    self.prev_filter_part_id = filter_part_id
    self.prev_filter_part_name = filter_part_name
    self.prev_filter_bin = filter_bin
    self.prev_filter_owner = filter_owner
    self.prev_filter_kanban = filter_kanban

    self.button_home.role = "mydefault-button"
    self.repeating_panel_inventory.role = "scrolling-panel"
    
    self.text_box_part_id.text = self.prev_filter_part_id
    self.text_box_part_name.text = self.prev_filter_part_name
        
    bin_options = [""] + anvil.server.call("get_inventory_bins")
    self.drop_down_bin.items = bin_options
    self.drop_down_bin.selected_value = self.prev_filter_bin
    
    owner_options = [""] + anvil.server.call("get_inventory_owners")
    self.drop_down_owner.items = owner_options
    self.drop_down_owner.selected_value = self.prev_filter_owner
    self.check_box_kanban.checked = self.prev_filter_kanban

    # Bind event handlers
    self.text_box_part_id.set_event_handler('change', self.update_filter)
    self.text_box_part_name.set_event_handler('change', self.update_filter)
    self.drop_down_bin.set_event_handler('change', self.update_filter)
    self.drop_down_owner.set_event_handler('change', self.update_filter)
    self.check_box_kanban.set_event_handler('change', self.update_filter)

    self.repeating_panel_inventory.set_event_handler("x-show-detail", self.show_detail)

    # Initial load
    self.update_filter()

  def update_filter(self, **event_args):
    self.prev_filter_part_id = self.text_box_part_id.text or ""
    self.prev_filter_part_name = self.text_box_part_name.text or ""
    self.prev_filter_bin = self.drop_down_bin.text or ""
    self.prev_filter_owner = self.drop_down_owner.selected_value or ""
    self.prev_filter_kanban = self.check_box_kanban.checked

    try:
      results = anvil.server.call(
        "get_filtered_inventory",
        part_id=self.prev_filter_part_id,
        part_name=self.prev_filter_part_name,
        bin=self.prev_filter_bin,
        owner=self.prev_filter_owner,
        is_kanban=self.prev_filter_kanban
      )
      self.repeating_panel_inventory.items = results
      self.label_count.text = f"{len(results)} rows returned"
    except Exception as e:
      self.label_count.text = f"Error: {e}"
      self.repeating_panel_inventory.items = []

  def show_detail(self, inventory_row, **event_args):
    try:
      open_form("InventoryRecord",
                inventory_part_id=inventory_row["part_id"],
                prev_filter_part_name=self.prev_filter_part_name,
                prev_filter_bin=self.prev_filter_bin,
                prev_filter_owner=self.prev_filter_owner,
                prev_filter_kanban=self.prev_filter_kanban)
    except Exception as e:
      alert(f"Error opening inventory detail: {e}")

  def button_home_click(self, **event_args):
    open_form("Nav")

