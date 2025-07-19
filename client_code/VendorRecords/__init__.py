from anvil import *
import anvil.server

from ._anvil_designer import VendorRecordsTemplate
from .. import config

class VendorRecords(VendorRecordsTemplate):
  def __init__(self, filter_vendor_id="", filter_company_name="", **kwargs):
    self.init_components(**kwargs)
    self.button_new_vendor.role = "new-button"
    self.grid_panel_1.role = "gridpanel-border"
    self.repeating_panel_1.role = "scrolling-panel"
    self.text_box_vendor_id.col_width = 4
    self.text_box_company_name.col_width = 5
    self.label_count.col_width = 3

    self.text_box_vendor_id.text = filter_vendor_id
    self.text_box_company_name.text = filter_company_name

    self.text_box_vendor_id.set_event_handler('change', self.update_filter)
    self.text_box_company_name.set_event_handler('change', self.update_filter)
    self.repeating_panel_1.set_event_handler("x-show-detail", self.show_detail)

    self.update_filter()

  def update_filter(self, **event_args):
    vendor_id = self.text_box_vendor_id.text.strip()
    company_name = self.text_box_company_name.text.strip()

    try:
      response = anvil.server.call(
        "get_filtered_vendors",
        vendor_id=vendor_id,
        company_name=company_name
      )
      self.repeating_panel_1.items = response
      self.label_count.text = f"✅ {len(response)} vendors returned"
    except Exception as e:
      self.label_count.text = f"❌ Error: {e}"
      self.repeating_panel_1.items = []

  def show_detail(self, vendor, **event_args):
    try:
      fresh_vendor = anvil.server.call("get_vendor", vendor["_id"])
    except Exception as e:
      Notification(f"⚠️ Could not refresh vendor: {e}", style="warning").show()
      fresh_vendor = vendor

    open_form("VendorRecord",
      vendor=fresh_vendor,
      prev_filter_vendor_id=self.text_box_vendor_id.text,
      prev_filter_company_name=self.text_box_company_name.text
    )

  def button_new_vendor_click(self, **event_args):
    open_form("VendorRecord",
      vendor=None,
      prev_filter_vendor_id=self.text_box_vendor_id.text,
      prev_filter_company_name=self.text_box_company_name.text
    )




