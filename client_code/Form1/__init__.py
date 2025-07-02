from anvil import *
import anvil.http

from ._anvil_designer import Form1Template
class Form1(Form1Template):
  def __init__(self, **properties):
    self.init_components(**properties)
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
        url=f"http://127.0.0.1:8000/parts?prefix={prefix}",
        method="GET",
        json=True
      )
      print(f"Raw response from server: {response}")

      filtered = [
        part for part in response
        if desc.lower() in (part.get("description") or "").lower()
      ]
      self.repeating_panel_1.items = filtered
      self.label_status.text = f"✅ {len(filtered)} parts found"
      
    except Exception as e:
      self.label_status.text = f"❌ Error: {e}"
      self.repeating_panel_1.items = []

  def show_detail(self, part, **event_args):
    open_form("PartDetail", part=part)

