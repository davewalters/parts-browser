from anvil import *
import anvil.http

from ._anvil_designer import VendorRecordsTemplate

class VendorRecords(VendorRecordsTemplate):
  def __init__(self, filter_vendor_id="", filter_company_name="", **kwargs):
    self.init_components(**kwargs)
    self.button_new_vendor.role = "new-button"

    self.text_box_vendor_id.text = filter_vendor_id
    self.text_box_company_name.text = filter_company_name

    self.grid_panel_1.role = "gridpanel-border"
    self.repeating_panel_1.role = "scrolling-panel"
    self.text_box_vendor_id.col_width = 4
    self.text_box_company_name.col_width = 5
    self.label_count.col_width = 3

    self.text_box_vendor_id.set_event_handler('change', self.update_filter)
    self.text_box_company_name.set_event_handler('change', self.update_filter)
    self.repeating_panel_1.set_event_handler("x-show-detail", self.show_detail)

    self.update_filter()

  def update_filter(self, **event_args):
    vendor_id = self.text_box_vendor_id.text.strip()
    company_name = self.text_box_company_name.text.strip()
  
    try:
      # Build URL query string
      params = []
      if vendor_id:
        params.append(f"vendor_id={vendor_id}")
      if company_name:
        params.append(f"company_name={company_name}")
      query_string = "&".join(params)
      print(query_string)
  
      url = "http://127.0.0.1:8000/vendors/full"
      if query_string:
        url += f"?{query_string}"
  
      response = anvil.http.request(url=url, method="GET", json=True)
      self.repeating_panel_1.items = response
      self.label_count.text = f"✅ {len(response)} vendors returned"
    except Exception as e:
      self.label_count.text = f"❌ Error: {e}"
      self.repeating_panel_1.items = []

  def show_detail(self, vendor, **event_args):
    open_form("VendorRecord",
              vendor=vendor,
              prev_filter_vendor_id=self.text_box_vendor_id.text,
              prev_filter_company_name=self.text_box_company_name.text)

  def button_new_vendor_click(self, **event_args):
    open_form("VendorRecord",
              vendor=None,
              prev_filter_vendor_id=self.text_box_vendor_id.text,
              prev_filter_company_name=self.text_box_company_name.text)

