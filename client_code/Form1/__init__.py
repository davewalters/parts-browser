from anvil import *
import anvil.http

class Form1(Form1):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.repeating_panel_1.items = []
    self.text_box_part_no.set_event_handler('change', self.update_filter)
    self.text_box_desc.set_event_handler('change', self.update_filter)
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
      filtered = [
        part for part in response
        if desc.lower() in (part.get("description") or "").lower()
      ]
      self.repeating_panel_1.items = filtered
    except Exception as e:
      self.label_status.text = f"❌ Error: {e}"
      self.repeating_panel_1.items = []

  def show_detail(self, part):
    open_form("PartDetail", part=part)
