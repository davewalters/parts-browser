#V.ItemTemplate2 - handles individual vendor rows for VendorsList

from ._anvil_designer import ItemTemplate2Template
from anvil import *
from .. import VendorsList
#from .. import VendorsDetail

class ItemTemplate2(ItemTemplate2Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.label_vendor_id.text = self.item.get("vendor_id", "")
    self.label_company_name.text = self.item.get("vendor_company_name", "")
    self.label_address_line1line1.text = self.item.get("address.line1", "")
    self.label_address_line2.text = self.item.get("address.line2", "")
    self.label_city.text = str(self.item.get("address.city", ""))

  def button_view_click(self, **event_args):
    self.parent.raise_event("x-edit-vendor", vendor_data=self.item)
