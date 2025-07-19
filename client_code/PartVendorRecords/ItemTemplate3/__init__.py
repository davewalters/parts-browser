from anvil import *
import anvil.server
from ._anvil_designer import ItemTemplate3Template

class ItemTemplate3(ItemTemplate3Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.radio_button_active_vendor.group_name = "vendor_active_group"
    self.radio_button_active_vendor.set_event_handler("change", self.radio_button_active_vendor_change)

    self.set_display_fields()

  def set_display_fields(self):
    item = self.item
    self.label_vendor_id.text = item.get("vendor_company_name", "")
    self.label_vendor_part_no.text = item.get("vendor_part_no", "")
    self.label_vendor_currency.text = item.get("vendor_currency", "")
    self.label_vendor_price.text = self.format_currency(item.get("vendor_price"))

    # Fallback to cost fields from vendor itself if no latest_cost dict
    cost_nz = item.get("cost_$NZ") or item.get("latest_cost", {}).get("cost_nz", None)
    cost_date = item.get("cost_date") or item.get("latest_cost", {}).get("cost_date", None)
    self.label_cost_nz.text = self.format_currency(cost_nz)
    self.label_cost_date.text = self.format_date(cost_date)

    is_active = item.get("is_active", False)
    self.radio_button_active_vendor.selected = is_active
    self.set_label_colors(is_active)

  def set_label_colors(self, is_active):
    color = "#000" if is_active else "#aaa"
    for lbl in [self.label_vendor_id, self.label_vendor_part_no,
                self.label_vendor_currency, self.label_vendor_price, 
                self.label_cost_nz, self.label_cost_date]:
      lbl.foreground = color

  def button_view_click(self, **event_args):
    self.parent.raise_event("x-edit-vendor", vendor_data=self.item)

  def radio_button_active_vendor_change(self, **event_args):
    if self.radio_button_active_vendor.selected:
      self.parent.raise_event("x-set-default-vendor", vendor_id=self.item.get("vendor_id"))

  def format_date(self, iso_string):
    """Return only the date portion of an ISO 8601 string, or epoch if blank."""
    if not iso_string or not isinstance(iso_string, str):
      return "1970-01-01"
    return iso_string.split("T")[0] if "T" in iso_string else iso_string

  def format_currency(self, value):
    """Format a float as NZ currency, or return '–' if invalid."""
    try:
      return f"${float(value):.2f}"
    except (ValueError, TypeError):
      return "–"

