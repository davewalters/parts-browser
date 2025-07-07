#V.ItemTemplate2 - handles individual vendor rows for VendorsList

from ._anvil_designer import ItemTemplate2Template
from anvil import *
from .. import VendorsList
#from .. import VendorsDetail

class ItemTemplate2(ItemTemplate2Template):
  def __init__(self, **properties):
    self.init_components(**properties)

    vendor = self.item
    self.label_vendor_id.text = vendor.get("_id", "")
    self.label_company_name.text = vendor.get("company_name", "")

    address = vendor.get("address", {})
    self.label_address_line1.text = address.get("line1", "")
    self.label_address_line2.text = address.get("line2", "")
    self.label_city.text = address.get("city", "")

  def button_view_click(self, **event_args):
    self.parent.raise_event("x-edit-vendor", vendor_data=self.item)
