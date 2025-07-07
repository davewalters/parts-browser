from anvil import *
import anvil.http

from ._anvil_designer import PartRecordsTemplate

class PartRecords(PartRecordsTemplate):
  def __init__(self, filter_part="", filter_desc="", **kwargs):
    #print(f"PartRecords.__init__ called with: filter_part={filter_part}, filter_desc={filter_desc}")
    self.init_components(**kwargs)
    self.button_new_part.role = "new-button"
    self.button_vendor_records.role = "mydefault-button"

    self.text_box_part_no.text = filter_part
    self.text_box_desc.text = filter_desc

    self.grid_panel_1.role = "gridpanel-border"
    self.repeating_panel_1.role = "scrolling-panel"
    self.text_box_part_no.col_width = 4
    self.text_box_desc.col_width = 5
    self.label_count.col_width = 3

    self.text_box_part_no.set_event_handler('change', self.update_filter)
    self.text_box_desc.set_event_handler('change', self.update_filter)
    self.repeating_panel_1.set_event_handler("x-show-detail", self.show_detail)

    try:
      self.update_filter()
    except Exception as e:
      alert(f"update_filter failed: {e}")

  def update_filter(self, **event_args):
    prefix = self.text_box_part_no.text or ""
    desc = self.text_box_desc.text or ""

    try:
      response = anvil.http.request(
        url=f"http://127.0.0.1:8000/parts?prefix={prefix}&desc={desc}",
        method="GET",
        json=True
      )
      self.repeating_panel_1.items = response
      self.label_count.text = f"✅ {len(response)} parts returned"
    except Exception as e:
      self.label_count.text = f"❌ Error: {e}"
      self.repeating_panel_1.items = []

  def show_detail(self, part, **event_args):
    # Use self.text_box_... directly
    open_form("PartRecord",
              part=part,
              prev_filter_part=self.text_box_part_no.text,
              prev_filter_desc=self.text_box_desc.text)

  def button_new_part_click(self, **event_args):
  # Create a new empty part
    open_form("PartRecord",
              part=None,
              prev_filter_part=self.text_box_part_no.text,
              prev_filter_desc=self.text_box_desc.text)

  def button_vendor_records_click(self, **event_args):
    open_form("VendorRecords")


