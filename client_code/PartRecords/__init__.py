from anvil import *
import anvil.server

from ._anvil_designer import PartRecordsTemplate
from .. import config

class PartRecords(PartRecordsTemplate):
  def __init__(self, filter_part="", filter_desc="", filter_type="", filter_status="", **kwargs):
    self.init_components(**kwargs)
    self.prev_filter_part = filter_part
    self.prev_filter_desc = filter_desc
    self.prev_filter_type = filter_type
    self.prev_filter_status = filter_status
    self.button_new_part.role = "new-button"

    self.text_box_part_no.text = filter_part
    self.text_box_desc.text = filter_desc
    self.drop_down_type.items = [""] + ["part", "assembly", "phantom", "material", "service", "documentation"]
    self.drop_down_status.items = [""] + ["active", "obsolete"]
    self.drop_down_type.selected_value = filter_type
    self.drop_down_status.selected_value = filter_status

    self.text_box_part_no.set_event_handler('change', self.update_filter)
    self.text_box_desc.set_event_handler('change', self.update_filter)
    self.drop_down_type.set_event_handler('change', self.update_filter)
    self.drop_down_status.set_event_handler('change', self.update_filter)
    self.repeating_panel_1.set_event_handler("x-show-detail", self.show_detail)

    self.update_filter()

  def update_filter(self, **event_args):
    self.prev_filter_part = self.text_box_part_no.text or ""
    self.prev_filter_desc = self.text_box_desc.text or ""
    self.prev_filter_type = self.drop_down_type.selected_value or ""
    self.prev_filter_status = self.drop_down_status.selected_value or ""

    try:
      results = anvil.server.call(
        "get_filtered_parts",
        prefix=self.prev_filter_part,
        desc=self.prev_filter_desc,
        part_type=self.prev_filter_type,
        status=self.prev_filter_status
      )
      self.repeating_panel_1.items = results
      self.label_count.text = f"{len(results)} parts returned"
    except Exception as e:
      self.label_count.text = f"Error: {e}"
      self.repeating_panel_1.items = []

  def show_detail(self, part, **event_args):
    # Always refresh from the server by ID to get the latest cost
    try:
      part_id = part["_id"]
      fresh_part = anvil.server.call("get_part", part_id)
      open_form("PartRecord",
                part=fresh_part,
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status)
    except Exception as e:
      alert(f"Error loading part detail: {e}")

  def button_new_part_click(self, **event_args):
    open_form("PartRecord",
              part=None,
              prev_filter_part=self.prev_filter_part,
              prev_filter_desc=self.prev_filter_desc,
              prev_filter_type=self.prev_filter_type,
              prev_filter_status=self.prev_filter_status)






