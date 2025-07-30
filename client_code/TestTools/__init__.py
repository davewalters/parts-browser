from ._anvil_designer import TestToolsTemplate
from anvil import *
import anvil.server

class TestTools(TestToolsTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_home.role = "mydefault-button"
    self.button_generate.role = "primary-button"
    self.button_delete.role = "destructive-button"

  def button_generate_click(self, **event_args):
    prefix = self.text_box_prefix.text or ""
    try:
      count = anvil.server.call("generate_inventory_records_from_parts", prefix)
      self.label_result.text = f"✅ {count} inventory rows created."
    except Exception as e:
      self.label_result.text = f"⚠️ Error: {e}"

  def button_delete_click(self, **event_args):
    try:
      count = anvil.server.call("delete_all_inventory")
      self.label_result.text = f"🗑️ {count} inventory rows deleted."
    except Exception as e:
      self.label_result.text = f"⚠️ Error: {e}"

  def button_home_click(self, **event_args):
    open_form("Nav")

