from anvil import *
from ._anvil_designer import CustomerRecordsRowTemplate

class CustomerRecordsRow(CustomerRecordsRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_details.role = "mydefault-button"
    self.label_customer_id.text = self.item.get("customer_id","")
    self.label_name.text = self.item.get("name","") or ""
    self.label_email.text = self.item.get("email","") or ""
    self.label_billing_address.text = self._format_billing_address(self.item)

  def _format_billing_address(self, item: dict) -> str:
    addrs = item.get("addresses") or []
    # Prefer default billing, else any billing
    billing = next((a for a in addrs if a.get("type")=="billing" and a.get("is_default")), None) \
    or next((a for a in addrs if a.get("type")=="billing"), None)
    if not billing:
      return ""
    lines = billing.get("address_lines") or []
    parts = []
    parts.extend([l for l in lines if l])
    parts.append(billing.get("locality") or "")
    parts.append(billing.get("administrative_area") or "")
    parts.append(billing.get("postal_code") or "")
    parts.append(billing.get("country_code") or "")
    return ", ".join([p for p in parts if p])

  def button_details_click(self, **event_args):
    open_form("CustomerRecord",
              customer_id=self.item.get("customer_id"),
              is_new=False,
             )

