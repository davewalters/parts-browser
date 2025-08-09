# forms/customers/CustomerRecord/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import CustomerRecordTemplate

_TAX_TYPES = ["GST", "VAT", "SalesTax", "ABN", "EIN", "Other"]
# keep a short starter set; you can load full ISO list later from server if preferred
_COUNTRIES = ["NZ", "AU", "GB", "IE", "DE", "FR", "NL", "US", "CA", "CN", "JP"]

class CustomerRecord(CustomerRecordTemplate):
  def __init__(self, customer_id=None, is_new=False, **properties):
    self.init_components(**properties)
    self.button_save.role = "save-button"
    self.button_back.role = "mydefault-button"
    self.button_delete.role = "delete-button"

    self.is_new = is_new
    self._original = None

    # Populate dropdowns
    self.drop_down_tax_type.items = _TAX_TYPES
    self.drop_down_tax_country_code.items = _COUNTRIES

    if self.is_new:
      self.button_delete.visible = False
      self._bind_blank()
    else:
      doc = anvil.server.call("get_customer", customer_id)
      self._original = doc
      self._bind_doc(doc)

  # ---- binding helpers ----
  def _bind_blank(self):
    # Core
    self.text_customer_id.text = ""
    self.text_name.text = ""
    self.text_legal_name.text = ""
    self.text_email.text = ""
    self.text_website.text = ""
    self.text_currency.text = "NZD"
    self.text_notes.text = ""

    # Phone (primary)
    self.text_phone_raw.text = ""
    self.text_phone_e164.text = ""

    # Contact (single)
    self.text_contact_name.text = ""
    self.text_contact_email.text = ""
    self.text_contact_phone_raw.text = ""
    self.text_contact_phone_e164.text = ""
    self.text_contact_role.text = ""

    # Addresses (billing + shipping)
    for p in ("b", "s"):
      getattr(self, f"text_{p}_name_line").text = ""
      getattr(self, f"text_{p}_org").text = ""
      getattr(self, f"text_{p}_addr1").text = ""
      getattr(self, f"text_{p}_addr2").text = ""
      getattr(self, f"text_{p}_locality").text = ""
      getattr(self, f"text_{p}_admin_area").text = ""
      getattr(self, f"text_{p}_postal_code").text = ""
      getattr(self, f"text_{p}_country_code").text = "NZ"

    # Tax registration (single visible row = default)
    self.drop_down_tax_country_code.selected_value = "NZ"
    self.drop_down_tax_type.selected_value = "GST"
    self.text_tax_id_number.text = ""
    self.check_tax_is_default.checked = True

  def _bind_doc(self, doc: dict):
    # Core
    self.text_customer_id.text = doc.get("customer_id", "")
    self.text_name.text = doc.get("name", "")
    self.text_legal_name.text = doc.get("legal_name", "") or ""
    self.text_email.text = doc.get("email", "") or ""
    self.text_website.text = doc.get("website", "") or ""
    self.text_currency.text = doc.get("currency", "NZD")
    self.text_notes.text = doc.get("notes", "") or ""

    # Phones (primary default)
    p = next((p for p in doc.get("phones", []) if p.get("is_default")), None)
    self.text_phone_raw.text = (p or {}).get("raw", "") or ""
    self.text_phone_e164.text = (p or {}).get("e164", "") or ""

    # Contact (first if present)
    c = (doc.get("contacts") or [])
    if c:
      c0 = c[0]
      self.text_contact_name.text = c0.get("name","") or ""
      self.text_contact_email.text = c0.get("email","") or ""
      ph = c0.get("phone") or {}
      self.text_contact_phone_raw.text = ph.get("raw","") or ""
      self.text_contact_phone_e164.text = ph.get("e164","") or ""
      self.text_contact_role.text = c0.get("role","") or ""
    else:
      self.text_contact_name.text = ""
      self.text_contact_email.text = ""
      self.text_contact_phone_raw.text = ""
      self.text_contact_phone_e164.text = ""
      self.text_contact_role.text = ""

    # Addresses (default billing & shipping)
    def _addr_of(kind):
      return next((a for a in doc.get("addresses", []) if a.get("type")==kind and a.get("is_default")), None)

    for kind, prefix in (("billing","b"), ("shipping","s")):
      addr = _addr_of(kind) or {}
      lines = addr.get("address_lines") or []
      getattr(self, f"text_{prefix}_name_line").text = addr.get("name_line","") or ""
      getattr(self, f"text_{prefix}_org").text = addr.get("organization","") or ""
      getattr(self, f"text_{prefix}_addr1").text = lines[0] if len(lines)>0 else ""
      getattr(self, f"text_{prefix}_addr2").text = lines[1] if len(lines)>1 else ""
      getattr(self, f"text_{prefix}_locality").text = addr.get("locality","") or ""
      getattr(self, f"text_{prefix}_admin_area").text = addr.get("administrative_area","") or ""
      getattr(self, f"text_{prefix}_postal_code").text = addr.get("postal_code","") or ""
      getattr(self, f"text_{prefix}_country_code").text = addr.get("country_code","NZ") or "NZ"

    # Tax registration (use default if any, else first)
    trs = doc.get("tax_registrations") or []
    tr = next((t for t in trs if t.get("is_default")), trs[0] if trs else None)
    if tr:
      self.drop_down_tax_country_code.selected_value = tr.get("country_code", "NZ")
      self.drop_down_tax_type.selected_value = tr.get("type", "Other")
      self.text_tax_id_number.text = tr.get("id_number","") or ""
      self.check_tax_is_default.checked = tr.get("is_default", True)
    else:
      self.drop_down_tax_country_code.selected_value = "NZ"
      self.drop_down_tax_type.selected_value = "GST"
      self.text_tax_id_number.text = ""
      self.check_tax_is_default.checked = True

  # ---- events ----
  def button_back_click(self, **event_args):
    open_form("CustomerRecords", filter_customer_id="", filter_name="")

  def button_delete_click(self, **event_args):
    try:
      cid = (self.text_customer_id.text or "").strip()
      if not cid:
        Notification("No customer_id to delete.", style="warning").show()
        return
      ok = anvil.server.call("delete_customer", cid)
      if ok:
        Notification("Customer deleted.", style="success").show()
        open_form("CustomerRecords")
      else:
        Notification("Delete failed or not found.", style="warning").show()
    except Exception as e:
      Notification(f"❌ Delete failed: {e}", style="danger").show()

  def button_save_click(self, **event_args):
    try:
      payload = self._collect_payload()
      doc = anvil.server.call("upsert_customer", payload)
      Notification("✅ Customer saved.", style="success").show()
      open_form(CustomerRecord(customer_id=doc["customer_id"], is_new=False))
    except Exception as e:
      Notification(f"❌ Save failed: {e}", style="danger").show()

  # ---- collect payload ----
  def _collect_payload(self) -> dict:
    cid = (self.text_customer_id.text or "").strip()
    if not cid:
      raise ValueError("customer_id is required")

    # Billing
    billing = {
      "type": "billing",
      "is_default": True,
      "organization": (self.text_b_org.text or "").strip() or None,
      "name_line": (self.text_b_name_line.text or "").strip() or None,
      "address_lines": list(filter(None, [
        (self.text_b_addr1.text or "").strip(),
        (self.text_b_addr2.text or "").strip()
      ])),
      "locality": (self.text_b_locality.text or "").strip() or None,
      "administrative_area": (self.text_b_admin_area.text or "").strip() or None,
      "postal_code": (self.text_b_postal_code.text or "").strip() or None,
      "country_code": (self.text_b_country_code.text or "NZ").strip() or "NZ",
    }

    # Shipping
    shipping = {
      "type": "shipping",
      "is_default": True,
      "organization": (self.text_s_org.text or "").strip() or None,
      "name_line": (self.text_s_name_line.text or "").strip() or None,
      "address_lines": list(filter(None, [
        (self.text_s_addr1.text or "").strip(),
        (self.text_s_addr2.text or "").strip()
      ])),
      "locality": (self.text_s_locality.text or "").strip() or None,
      "administrative_area": (self.text_s_admin_area.text or "").strip() or None,
      "postal_code": (self.text_s_postal_code.text or "").strip() or None,
      "country_code": (self.text_s_country_code.text or "NZ").strip() or "NZ",
    }

    # Primary phone
    primary_phone = {
      "type": "primary",
      "is_default": True,
      "raw": (self.text_phone_raw.text or "").strip() or None,
      "e164": (self.text_phone_e164.text or "").strip() or None,
    }

    # Single contact (optional)
    contact = None
    if (self.text_contact_name.text or "").strip():
      contact = {
        "name": (self.text_contact_name.text or "").strip(),
        "email": (self.text_contact_email.text or "").strip() or None,
        "role": (self.text_contact_role.text or "").strip() or None,
        "phone": {
          "type": "other",
          "is_default": False,
          "raw": (self.text_contact_phone_raw.text or "").strip() or None,
          "e164": (self.text_contact_phone_e164.text or "").strip() or None,
        }
      }

    # Default tax registration (single row)
    tr = {
      "country_code": self.drop_down_tax_country_code.selected_value or "NZ",
      "type": self.drop_down_tax_type.selected_value or "Other",
      "id_number": (self.text_tax_id_number.text or "").strip(),
      "is_default": True if self.check_tax_is_default.checked else True  # single row => default
    }
    tax_registrations = [tr] if tr["id_number"] else []

    payload = {
      "customer_id": cid,
      "name": (self.text_name.text or "").strip(),
      "legal_name": (self.text_legal_name.text or "").strip() or None,
      "email": (self.text_email.text or "").strip() or None,
      "website": (self.text_website.text or "").strip() or None,
      "currency": (self.text_currency.text or "NZD").strip() or "NZD",
      "addresses": [billing, shipping],
      "phones": [primary_phone] if (primary_phone["raw"] or primary_phone["e164"]) else [],
      "contacts": [contact] if contact else [],
      "tax_registrations": tax_registrations,
      "notes": (self.text_notes.text or "").strip() or None,
    }
    return payload

