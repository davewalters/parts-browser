# PartDetail.py (Editable form)
from anvil import *
import anvil.http
from ._anvil_designer import PartDetailTemplate
from math import isnan

def clean_value(value):
  if value is None:
    return ""
  if isinstance(value, float) and math.isnan(value):
    return ""
  return value

class PartDetail(PartDetailTemplate):
  def __init__(self, part=None, new=False, **properties):
    self.init_components(**properties)

    self.part = part or {}
    self.is_new = new
    self.label_title.text = "New Part" if new else f"Edit Part: {self.part.get('_id', '')}"

    # Fill form fields if editing
    if not new and part:
      self.text_box_id.text = part.get("_id", "")
      self.text_box_desc.text = part.get("description", "")
      self.text_box_rev.text = part.get("revision", "")
      self.text_box_status.text = part.get("status", "")
      self.text_box_vendor.text = part.get("default_vendor", "")
      self.text_box_type.text = part.get("type", "")
      self.text_box_process.text = part.get("process", "")
      self.text_box_material.text = part.get("material_spec", "")
      self.text_box_unit.text = part.get("unit", "")
      cost = part.get("latest_cost", {})
      self.text_box_cost.text = str(cost.get("cost_nz") or "")
      self.text_box_cost_date.text = str(cost.get("cost_date") or "")

    self.text_box_id.enabled = new  # Lock ID if editing
  
  def button_save_click(self, **event_args):
    # Construct latest_cost dictionary with safe defaults
    latest_cost = {
      "cost_nz": 0.0,
      "cost_date": "1970-01-01"  # Default epoch date
    }
    latest_cost["cost_date"] = self.text_box_cost_date.text or "1970-01-01"
    
    new_data = {
      "_id": self.text_box_id.text,
      "description": clean_value(self.text_box_desc.text),
      "revision": clean_value(self.text_box_rev.text),
      "status": clean_value(self.text_box_status.text),
      "default_vendor": clean_value(self.text_box_vendor.text),
      "type": clean_value(self.text_box_type.text),
      "process": clean_value(self.text_box_process.text),
      "material_spec": clean_value(self.text_box_material.text),
      "unit": clean_value(self.text_box_unit.text),
      "latest_cost": latest_cost,
      "vendor_part_numbers": self.part.get("vendor_part_numbers", [])
    }

    try:
      if self.is_new:
        url = "http://127.0.0.1:8000/parts"
        method = "POST"
      else:
        url = f"http://127.0.0.1:8000/parts/{self.part['_id']}"
        method = "PUT"
      print("📤 Sending to FastAPI:", new_data)

      anvil.http.request(
        url=url,
        method=method,
        json=new_data
      )
      Notification("✅ Part saved.", style="success").show()
      open_form("Form1")
    except Exception as e:
      Notification(f"❌ Save failed: {e}", style="danger").show()

  def button_back_click(self, **event_args):
    open_form("Form1")
