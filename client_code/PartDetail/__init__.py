from anvil import *

from ._anvil_designer import PartDetailTemplate
class PartDetail(PartDetailTemplate):
  def __init__(self, part=None, **properties):
    self.init_components(**properties)
    self.label_id.text = part.get("_id", "")
    self.label_rev.text = part.get("revision", "")
    self.label_desc.text = part.get("description", "")
    self.label_status.text = part.get("status", "")
    self.label_vendor.text = part.get("default_vendor", "")

  def button_back_click(self, **event_args):
    open_form("Form1")
