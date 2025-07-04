# PartDetail.py (Editable form)
from anvil import *
import anvil.http
from ._anvil_designer import PartDetailTemplate
from math import isnan

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

  def clean_value(self, value):
    if value is None:
      return ""
    if isinstance(value, float) and math.isnan(value):
      return ""
    return value

  def clean_vendor_part_numbers(self, vendor_parts):
    cleaned = []
    for vp in vendor_parts:
      if not isinstance(vp, dict):
        continue
      cleaned.append({
        "vendor_id": self.clean_value(vp.get("vendor_id")),
        "vendor_part_no": self.clean_value(vp.get("vendor_part_no")),
        "vendor_currency": self.clean_value(vp.get("vendor_currency")),
        "vendor_price": vp.get("vendor_price") or 0.0,
        "cost_$NZ": vp.get("cost_$NZ") or 0.0,
        "cost_date": self.clean_value(vp.get("cost_date")) or "1970-01-01"
      })
    return cleaned
  
  def button_save_click(self, **event_args):
    # Construct latest_cost dictionary with safe defaults
    latest_cost = {
      "cost_nz": 0.0,
      "cost_date": "1970-01-01"  # Default epoch date
    }

    if self.text_box_cost.text:
      try:
        latest_cost["cost_nz"] = float(self.text_box_cost.text)
      except ValueError:
        pass

    if self.text_box_cost_date.text:
      latest_cost["cost_date"] = self.text_box_cost_date.text or "1970-01-01"

    new_data = {
      "_id": self.text_box_id.text,
      "description": self.clean_value(self.text_box_desc.text),
      "revision": self.clean_value(self.text_box_rev.text),
      "status": self.clean_value(self.text_box_status.text),
      "default_vendor": self.clean_value(self.text_box_vendor.text),
      "type": self.clean_value(self.text_box_type.text),
      "process": self.clean_value(self.text_box_process.text),
      "material_spec": self.clean_value(self.text_box_material.text),
      "unit": self.clean_value(self.text_box_unit.text),
      "latest_cost": latest_cost,
      "vendor_part_numbers": self.clean_vendor_part_numbers(self.part.get("vendor_part_numbers", []))
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
