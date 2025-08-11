# forms/customers/CustomerRecord/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import CustomerRecordTemplate
from .. CustomerRecords import CustomerRecords

_TAX_TYPES = ["GST", "VAT", "SalesTax", "ABN", "EIN", "Other"]
_COUNTRIES = ["NZ", "AU", "GB", "IE", "DE", "FR", "NL", "US", "CA", "CN", "JP"]
_CURRENCIES = ["NZD", "AUD", "GBP", "EUR", "USD", "CAD", "CNY", "JPY"]

class CustomerRecord(CustomerRecordTemplate):
  def __init__(self, customer_id=None, is_new=False, **properties):
    self.init_components(**properties)

    # Header + button styling
    self.header_panel.role = "sticky-header"
    self.button_save.role = "save-button"
    self.button_back.role = "mydefault-button"
    self.button_delete.role = "delete-button"

    self.is_new = is_new
    self._original = None

    # Contact prefill guards (per-field)
    self._contacts_prefilled_once = False
    self._contact_name_touched = False
    self._contact_email_touched = False
    self._contact_phone_raw_touched = False
    self._contact_phone_e164_touched = False

    # Populate dropdowns
    self.drop_down_tax_country_code.items = _COUNTRIES
    self.drop_down_tax_type.items = _TAX_TYPES
    self.drop_down_billing_country_code.items = _COUNTRIES
    self.drop_down_shipping_country_code.items = _COUNTRIES
    self.drop_down_currency.items = _CURRENCIES

    # Wire events
    self._wire_billing_sync_events()
    self._wire_contact_touched_events()
    self._wire_contact_prefill_events()

    if self.is_new:
      self.button_delete.visible = False
      self._bind_blank()

      # Auto-generate customer_id
      try:
        self.text_customer_id.text = anvil.server.call("generate_next_customer_id")
      except Exception as e:
        Notification(f"Could not auto-generate customer ID: {e}", style="warning").show()

      # Seed contacts once on first entry
      self._maybe_prefill_contacts_once(force=True)
    else:
      doc = anvil.server.call("get_customer", customer_id)
      if not doc:
        # Treat as new if not found / empty collection
        self.is_new = True
        self.button_delete.visible = False
        self._bind_blank()
        try:
          self.text_customer_id.text = anvil.server.call("generate_next_customer_id")
        except Exception as e:
          Notification(f"Could not auto-generate customer ID: {e}", style="warning").show()
        self._maybe_prefill_contacts_once(force=True)
      else:
        self._original = doc
        self._bind_doc(doc)

  # ---------- Bind helpers ----------
  def _bind_blank(self):
    # Core
    self.text_customer_id.text = ""
    self.text_name.text = ""
    self.text_legal_name.text = ""
    self.text_email.text = ""
    self.text_website.text = ""
    self.drop_down_currency.selected_value = "NZD"
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
    self._contacts_prefilled_once = False
    self._contact_name_touched = False
    self._contact_email_touched = False
    self._contact_phone_raw_touched = False
    self._contact_phone_e164_touched = False

    # Addresses (billing + shipping)
    for p in ("b", "s"):
      getattr(self, f"text_{p}_name_line").text = ""
      getattr(self, f"text_{p}_org").text = ""
      getattr(self, f"text_{p}_addr1").text = ""
      getattr(self, f"text_{p}_addr2").text = ""
      getattr(self, f"text_{p}_locality").text = ""
      getattr(self, f"text_{p}_admin_area").text = ""
      getattr(self, f"text_{p}_postal_code").text = ""

    self.drop_down_billing_country_code.selected_value = "NZ"
    self.drop_down_shipping_country_code.selected_value = "NZ"

    # Tax registration
    self.drop_down_tax_country_code.selected_value = "NZ"
    self.drop_down_tax_type.selected_value = "GST"
    self.text_tax_id_number.text = ""
    self.check_tax_is_default.checked = True

    # Same-as-billing default ON
    self.check_box_same_as_billing.checked = True
    self._sync_shipping_from_billing()

  def _bind_doc(self, doc: dict):
    if not doc:
      self._bind_blank()
      return

    # Core
    self.text_customer_id.text = doc.get("customer_id", "") or ""
    self.text_name.text = doc.get("name", "") or ""
    self.text_legal_name.text = doc.get("legal_name", "") or ""
    self.text_email.text = doc.get("email", "") or ""
    self.text_website.text = doc.get("website", "") or ""
    self.drop_down_currency.selected_value = doc.get("currency", "NZD")
    self.text_notes.text = doc.get("notes", "") or ""

    # Phones
    p = next((p for p in doc.get("phones", []) if p.get("is_default")), None)
    self.text_phone_raw.text = (p or {}).get("raw", "") or ""
    self.text_phone_e164.text = (p or {}).get("e164", "") or ""

    # Contact
    c = (doc.get("contacts") or [])
    if c:
      c0 = c[0]
      self.text_contact_name.text = c0.get("name","") or ""
      self.text_contact_email.text = c0.get("email","") or ""
      ph = c0.get("phone") or {}
      self.text_contact_phone_raw.text = ph.get("raw","") or ""
      self.text_contact_phone_e164.text = ph.get("e164","") or ""
      self.text_contact_role.text = c0.get("role","") or ""
      self._contacts_prefilled_once = True
      self._contact_name_touched = True
      self._contact_email_touched = True
      self._contact_phone_raw_touched = True
      self._contact_phone_e164_touched = True
    else:
      self._bind_blank()

    # Addresses
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

    self.drop_down_billing_country_code.selected_value = (_addr_of("billing") or {}).get("country_code", "NZ")
    self.drop_down_shipping_country_code.selected_value = (_addr_of("shipping") or {}).get("country_code", "NZ")

    # Tax registration
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

    self.check_box_same_as_billing.checked = True

  # ---------- Events ----------
  def button_back_click(self, **event_args):
    open_form("CustomerRecords")

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
      # Safety: prefill any untouched & empty contact fields
      self._maybe_prefill_single("text_name","text_contact_name","_contact_name_touched")
      self._maybe_prefill_single("text_email","text_contact_email","_contact_email_touched")
      self._maybe_prefill_single("text_phone_raw","text_contact_phone_raw","_contact_phone_raw_touched")
      self._maybe_prefill_single("text_phone_e164","text_contact_phone_e164","_contact_phone_e164_touched")

      payload = self._collect_payload()
      doc = anvil.server.call("upsert_customer", payload)
      Notification("✅ Customer saved.", style="success").show()
      open_form(CustomerRecord(customer_id=doc["customer_id"], is_new=False))
    except Exception as e:
      Notification(f"❌ Save failed: {e}", style="danger").show()

  # ---------- Billing -> Shipping sync ----------
  def _wire_billing_sync_events(self):
    fields = [
      "text_b_name_line","text_b_org","text_b_addr1","text_b_addr2",
      "text_b_locality","text_b_admin_area","text_b_postal_code"
    ]
    for name in fields:
      w = getattr(self, name, None)
      if w:
        w.set_event_handler("pressed_enter", self._maybe_sync_shipping)
        w.set_event_handler("lost_focus", self._maybe_sync_shipping)
    self.drop_down_billing_country_code.set_event_handler("change", self._maybe_sync_shipping)
    self.check_box_same_as_billing.set_event_handler("change", self._check_same_as_billing_changed)

  def _check_same_as_billing_changed(self, **event_args):
    if self.check_box_same_as_billing.checked:
      self._sync_shipping_from_billing()

  def _maybe_sync_shipping(self, **event_args):
    if self.check_box_same_as_billing.checked:
      self._sync_shipping_from_billing()

  def _sync_shipping_from_billing(self):
    self.text_s_name_line.text = self.text_b_name_line.text
    self.text_s_org.text = self.text_b_org.text
    self.text_s_addr1.text = self.text_b_addr1.text
    self.text_s_addr2.text = self.text_b_addr2.text
    self.text_s_locality.text = self.text_b_locality.text
    self.text_s_admin_area.text = self.text_b_admin_area.text
    self.text_s_postal_code.text = self.text_b_postal_code.text
    self.drop_down_shipping_country_code.selected_value = self.drop_down_billing_country_code.selected_value

  # ---------- Contact prefill wiring ----------
  def _wire_contact_touched_events(self):
    mapping = [
      ("text_contact_name", "_contact_name_touched"),
      ("text_contact_email", "_contact_email_touched"),
      ("text_contact_phone_raw", "_contact_phone_raw_touched"),
      ("text_contact_phone_e164", "_contact_phone_e164_touched"),
    ]
    for dest_attr, flag in mapping:
      w = getattr(self, dest_attr, None)
      if w:
        w.set_event_handler("change", lambda f=flag, **ea: setattr(self, f, True))
        w.set_event_handler("lost_focus", lambda f=flag, **ea: setattr(self, f, True))

  def _wire_contact_prefill_events(self):
    pairs = [
      ("text_name",       "text_contact_name",       "_contact_name_touched"),
      ("text_email",      "text_contact_email",      "_contact_email_touched"),
      ("text_phone_raw",  "text_contact_phone_raw",  "_contact_phone_raw_touched"),
      ("text_phone_e164", "text_contact_phone_e164", "_contact_phone_e164_touched"),
    ]
    for src_attr, dest_attr, flag in pairs:
      src = getattr(self, src_attr, None)
      if src:
        src.set_event_handler("pressed_enter",
                              lambda f=flag, s=src_attr, d=dest_attr, **ea: self._maybe_prefill_single(s, d, f))
        src.set_event_handler("lost_focus",
                              lambda f=flag, s=src_attr, d=dest_attr, **ea: self._maybe_prefill_single(s, d, f))

  def _maybe_prefill_single(self, src_attr, dest_attr, touched_flag, force=False):
    if not self.is_new:
      return
    dest_w = getattr(self, dest_attr)
    src_w  = getattr(self, src_attr)
    touched = getattr(self, touched_flag)
    if force or (not touched and not (dest_w.text or "").strip()):
      dest_w.text = (src_w.text or "").strip()

  def _maybe_prefill_contacts_once(self, force=False, **event_args):
    if not self.is_new:
      return
    all_blank = not any([
      (self.text_contact_name.text or "").strip(),
      (self.text_contact_email.text or "").strip(),
      (self.text_contact_phone_raw.text or "").strip(),
      (self.text_contact_phone_e164.text or "").strip(),
    ])
    if force or all_blank:
      self._maybe_prefill_single("text_name",       "text_contact_name",       "_contact_name_touched",       force=True)
      self._maybe_prefill_single("text_email",      "text_contact_email",      "_contact_email_touched",      force=True)
      self._maybe_prefill_single("text_phone_raw",  "text_contact_phone_raw",  "_contact_phone_raw_touched",  force=True)
      self._maybe_prefill_single("text_phone_e164", "text_contact_phone_e164", "_contact_phone_e164_touched", force=True)
      self._contacts_prefilled_once = True

  # ---------- Collect payload ----------
  def _collect_payload(self) -> dict:
    cid = (self.text_customer_id.text or "").strip()
    if not cid:
      raise ValueError("customer_id is required")

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
      "country_code": self.drop_down_billing_country_code.selected_value or "NZ",
    }

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
      "country_code": self.drop_down_shipping_country_code.selected_value or "NZ",
    }

    primary_phone = {
      "type": "primary",
      "is_default": True,
      "raw": (self.text_phone_raw.text or "").strip() or None,
      "e164": (self.text_phone_e164.text or "").strip() or None,
    }

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

    tr = {
      "country_code": self.drop_down_tax_country_code.selected_value or "NZ",
      "type": self.drop_down_tax_type.selected_value or "Other",
      "id_number": (self.text_tax_id_number.text or "").strip(),
      "is_default": True if self.check_tax_is_default.checked else True
    }
    tax_registrations = [tr] if tr["id_number"] else []

    return {
      "customer_id": cid,
      "name": (self.text_name.text or "").strip(),
      "legal_name": (self.text_legal_name.text or "").strip() or None,
      "email": (self.text_email.text or "").strip() or None,
      "website": (self.text_website.text or "").strip() or None,
      "currency": (self.drop_down_currency.selected_value or "NZD").strip() or "NZD",
      "notes": (self.text_notes.text or "").strip() or None,
      "phones": [primary_phone] if primary_phone["raw"] or primary_phone["e164"] else [],
      "contacts": [contact] if contact else [],
      "addresses": [billing, shipping],
      "tax_registrations": tax_registrations
    }






