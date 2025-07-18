# V.ItemTemplate3 - handles individual vendor rows

from anvil import *
import anvil.server
from ._anvil_designer import ItemTemplate3Template
from .. import PartVendorRecords
from .. import PartVendorRecord

class ItemTemplate3(ItemTemplate3Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.radio_button_active_vendor.group_name = "vendor_active_group"
    self.radio_button_active_vendor.set_event_handler("change", self.radio_button_active_vendor_change)

    self.label_vendor_id.text = self.item.get("vendor_company_name", "")
    self.label_vendor_part_no.text = self.item.get("vendor_part_no", "")
    self.label_vendor_currency.text = self.item.get("vendor_currency", "")
    self.label_vendor_price.text = str(self.item.get("vendor_price", ""))

    latest_cost = self.item.get("latest_cost", {})
    cost_nz = latest_cost.get("cost_nz", None)
    cost_date = latest_cost.get("cost_date", None)
    self.label_cost_nz.text = self.format_currency(cost_nz)
    self.label_cost_date.text = self.format_date(cost_date)

    is_active = self.item.get("is_active", False)
    color = "#000" if is_active else "#aaa"  # grey out inactive
    
    for lbl in [self.label_vendor_id, self.label_vendor_part_no,
                self.label_vendor_currency, self.label_vendor_price, 
                self.label_cost_NZD, self.label_cost_date]:
      lbl.foreground = color

    self.radio_button_active_vendor.selected = is_active

  def button_view_click(self, **event_args):
    self.parent.raise_event("x-edit-vendor", vendor_data=self.item)

  def radio_button_active_vendor_change(self, **event_args):
    if self.radio_button_active_vendor.selected:
      self.parent.raise_event("x-set-default-vendor", vendor_id=self.item.get("vendor_id"))

  def format_date(self, iso_string):
    """Return only the date portion of an ISO 8601 string."""
    return iso_string.split("T")[0] if "T" in iso_string else iso_string

  def format_currency(self, value):
    """Format a float as NZ currency, or return '–' if invalid."""
    try:
      return f"${float(value):.2f}"
    except (ValueError, TypeError):
      return "–"
