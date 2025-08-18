from anvil import *
import anvil.server
from ._anvil_designer import ItemTemplate1Template

class ItemTemplate1(ItemTemplate1Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.set_display_fields()

  def set_display_fields(self):
    part = self.item or {}
    self.label_id.text = part.get("_id", "")
    self.label_rev.text = part.get("revision", "")
    self.label_desc.text = part.get("description", "")
    self.label_status.text = part.get("status", "")
    self.label_type.text = part.get("type", "")
    self.label_type.column = "type"
    self.label_vendor.text = part.get("_vendor_name", part.get("default_vendor", ""))
  
    latest_cost = part.get("latest_cost", {}) or {}
    self.label_cost_nz.text = self.format_currency(latest_cost.get("cost_nz"))
    self.label_cost_date.text = self.format_date(latest_cost.get("cost_date"))

  def button_view_click(self, **event_args):
    self.parent.raise_event("x-show-detail", part=self.item)

  def format_date(self, iso_string):
    """Return only the date portion of an ISO 8601 string, or fallback."""
    if not iso_string or not isinstance(iso_string, str):
      return "1970-01-01"
    return iso_string.split("T")[0] if "T" in iso_string else iso_string

  def format_currency(self, value):
    """Format a float as NZ currency, or return '–' if invalid."""
    try:
      return f"${float(value):.2f}"
    except (ValueError, TypeError):
      return "–"




