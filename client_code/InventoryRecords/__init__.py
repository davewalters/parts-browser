from anvil import *
import anvil.server
from ._anvil_designer import InventoryRecordsTemplate

class InventoryRecords(InventoryRecordsTemplate):
  def __init__(self,
               filter_part_id="",
               filter_part_name="",
               filter_kanban=None,
               **kwargs):
    self.init_components(**kwargs)

    self.prev_filter_part_id = filter_part_id
    self.prev_filter_part_name = filter_part_name
    self.prev_filter_kanban = filter_kanban

    self.text_box_part_id.text = self.prev_filter_part_id
    self.text_box_part_name.text = self.prev_filter_part_name
    self.check_box_kanban.checked = self.prev_filter_kanban

    self.repeating_panel_inventory.role = "scrolling-panel"
    self.repeating_panel_inventory.set_event_handler("x-show-detail", self.show_detail)

    self.text_box_part_id.set_event_handler('change', self.update_filter)
    self.text_box_part_name.set_event_handler('change', self.update_filter)
    self.check_box_kanban.set_event_handler('change', self.update_filter)

    self.button_home.role = "mydefault-button"
    self.update_filter()

  def update_filter(self, **event_args):
    try:
      results = anvil.server.call(
        "get_inventory_summary",
        part_id=self.text_box_part_id.text or "",
        part_name=self.text_box_part_name.text or "",
        is_kanban=self.check_box_kanban.checked
      )
      self.repeating_panel_inventory.items = results
      self.label_count.text = f"{len(results)} parts returned"
    except Exception as e:
      self.label_count.text = f"Error: {e}"
      self.repeating_panel_inventory.items = []

  def show_detail(self, part_summary, **event_args):
    open_form("InventoryTransfers",
              inventory_part_id=part_summary["part_id"],
              prev_filter_part_id=self.text_box_part_id.text,
              prev_filter_part_name=self.text_box_part_name.text,
              prev_filter_kanban=self.check_box_kanban.checked)

  def button_home_click(self, **event_args):
    open_form("Nav")



