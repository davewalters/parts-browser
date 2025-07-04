from anvil import *
import anvil.http

from ._anvil_designer import Form1Template
class Form1(Form1Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.repeating_panel_1.role = "scrolling-panel"
    self.text_box_part_no.col_width = 4   # About 1/3 of the width
    self.text_box_desc.col_width = 5      # Slightly wider
    self.label_count.col_width = 3       # Remaining space
    self.repeating_panel_1.items = []
    self.text_box_part_no.set_event_handler('change', self.update_filter)
    self.text_box_desc.set_event_handler('change', self.update_filter)
    self.repeating_panel_1.set_event_handler("x-show-detail", self.show_detail)
    self.update_filter()


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
      self.label_count.text = f"✅ {len(response)} parts found"
    except Exception as e:
      self.label_count.text = f"❌ Error: {e}"
      self.repeating_panel_1.items = []


  def show_detail(self, part, **event_args):
    print("📦 show_detail triggered with part:", part.get("_id"))
    open_form("PartDetail", part=part)


