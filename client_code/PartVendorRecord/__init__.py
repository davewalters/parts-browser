from anvil import *
import anvil.server
from ._anvil_designer import PartVendorRecordTemplate
from datetime import datetime, date

class PartVendorRecord(PartVendorRecordTemplate):
  def __init__(self, part_id,
               vendor_data=None,
               prev_filter_part="",
               prev_filter_desc="",
               prev_filter_type="",
               prev_filter_status="",
               prev_filter_designbom=False,
               back_to_bom=False,
               back_to_po=False,
               purchase_order_id=None,
               assembly_part_id=None,
               return_to: dict | None = None,   # <<< NEW
               **kwargs):
    self.init_components(**kwargs)
    self.button_save.role = "save-button"
    self.button_back.role = "mydefault-button"
    self.button_delete_vendor.role = "delete-button"

    # NEW: unified return target
    self._return_to = return_to or None

    # Load part and initial vendor_data
    self.part = anvil.server.call("get_part", part_id)
    self.vendor_data = vendor_data or {
      "vendor_id": "",
      "vendor_part_no": "",
      "vendor_currency": "NZD",
      "vendor_price": 0.0,
      "cost_$NZ": 0.0,
      "cost_date": datetime.today().date().isoformat(),
    }

    # Nav context
    self.prev_filter_part = prev_filter_part
    self.prev_filter_desc = prev_filter_desc
    self.prev_filter_type = prev_filter_type
    self.prev_filter_status = prev_filter_status
    self.prev_filter_designbom = prev_filter_designbom
    self.back_to_bom = back_to_bom
    self.back_to_po = back_to_po
    self.purchase_order_id = purchase_order_id
    self.assembly_part_id = assembly_part_id or self.part.get("_id", "")

    # Build dropdown: (company_name, vendor_id)
    try:
      vendor_list = anvil.server.call("get_all_vendors") or []
      self._vendor_name_by_id = {
        v.get("vendor_id"): (v.get("company_name") or v.get("vendor_id"))
        for v in vendor_list if v.get("vendor_id")
      }
      self.drop_down_vendor_id.items = [
        (self._vendor_name_by_id[vid], vid) for vid in self._vendor_name_by_id.keys()
      ]
    except Exception as e:
      Notification(f"⚠️ Could not load vendor list: {e}", style="warning").show()
      self._vendor_name_by_id = {}
      self.drop_down_vendor_id.items = []

    # Currency dropdown (standardised)
    self.drop_down_vendor_currency.items = ["NZD", "USD", "AUD", "EUR", "GBP", "SGD"]

    # Active vendor delete guard (cannot delete the currently active/default vendor)
    is_active = self.vendor_data.get("vendor_id") == self.part.get("default_vendor", "")
    self.button_delete_vendor.visible = not is_active

    # Populate fields
    self.label_id.text = self.part.get("_id", "")
    self.label_id.role = "label-border"

    self.drop_down_vendor_id.selected_value = self.vendor_data.get("vendor_id") or None
    self.text_box_vendor_part_no.text = str(self.vendor_data.get("vendor_part_no", ""))
    self.drop_down_vendor_currency.selected_value = self.vendor_data.get("vendor_currency", "NZD")
    self.text_box_vendor_price.text = self._fmt_num(self.vendor_data.get("vendor_price", 0.0))
    self.label_cost_date.text = self._fmt_date(self.vendor_data.get("cost_date"))
    self.label_exchange_rate.text = f"Rate: {self._get_exchange_rate(self.drop_down_vendor_currency.selected_value)}"

    # Events
    self.text_box_vendor_price.set_event_handler("change", self._price_or_currency_changed)
    self.drop_down_vendor_currency.set_event_handler("change", self._price_or_currency_changed)

    # Initial NZD cost calc
    self._update_cost_nz()

  # ---------- FX helpers (placeholder static rates) ----------
  def _get_exchange_rate(self, currency: str) -> float:
    rates = {"NZD": 1.0, "USD": 1.65, "AUD": 1.08, "EUR": 1.94, "GBP": 2.25, "SGD": 1.29}
    return rates.get(currency or "NZD", 1.0)

  # ---------- UI updates ----------
  def _price_or_currency_changed(self, **event_args):
    self.label_exchange_rate.text = f"Rate: {self._get_exchange_rate(self.drop_down_vendor_currency.selected_value)}"
    self._update_cost_nz()

  def _update_cost_nz(self):
    try:
      price = float((self.text_box_vendor_price.text or "").replace("$", "").replace(",", "").strip() or 0.0)
      rate = self._get_exchange_rate(self.drop_down_vendor_currency.selected_value)
      cost_nz = round(price * rate, 2)
      self.vendor_data["vendor_price"] = price
      self.vendor_data["vendor_currency"] = self.drop_down_vendor_currency.selected_value or "NZD"
      self.vendor_data["cost_$NZ"] = cost_nz
      self.vendor_data["cost_date"] = datetime.today().date().isoformat()
      self.label_cost_nz.text = self._fmt_money(cost_nz)
      self.label_cost_date.text = self._fmt_date(self.vendor_data["cost_date"])
    except Exception:
      self.label_cost_nz.text = "–"

  # ---------- Save/Delete ----------
  def button_save_click(self, **event_args):
    self.vendor_data.update({
      "vendor_id": self.drop_down_vendor_id.selected_value or "",
      "vendor_part_no": (self.text_box_vendor_part_no.text or "").strip(),
      "vendor_currency": self.drop_down_vendor_currency.selected_value or "NZD",
      "vendor_price": self._parse_num(self.text_box_vendor_price.text),
    })

    if self.part.get("default_vendor") != self.vendor_data["vendor_id"]:
      self.part["default_vendor"] = self.vendor_data["vendor_id"]

    updated = False
    vpns = list(self.part.get("vendor_part_numbers", []))
    for idx, v in enumerate(vpns):
      if v.get("vendor_id") == self.vendor_data["vendor_id"]:
        vpns[idx] = dict(self.vendor_data)
        updated = True
        break
    if not updated:
      vpns.append(dict(self.vendor_data))
    self.part["vendor_part_numbers"] = vpns

    self.part["latest_cost"] = {
      "cost_nz": self.vendor_data.get("cost_$NZ", 0.0),
      "cost_date": self.vendor_data.get("cost_date", datetime.today().date().isoformat()),
    }

    try:
      for v in self.part["vendor_part_numbers"]:
        v.pop("vendor_company_name", None)
        v.pop("is_active", None)

      anvil.server.call("save_part_from_client", self.part)
      vname = self._vendor_name_by_id.get(self.vendor_data["vendor_id"], self.vendor_data["vendor_id"])
      Notification(f"✅ Saved vendor '{vname}' for part.", style="success").show()
    except Exception as e:
      Notification(f"❌ Failed to save vendor: {e}", style="danger", timeout=None).show()

  def button_delete_vendor_click(self, **event_args):
    vendor_id = self.vendor_data.get("vendor_id", "")
    if not vendor_id:
      Notification("⚠️ No vendor selected for deletion.", style="warning").show()
      return

    vname = self._vendor_name_by_id.get(vendor_id, vendor_id)
    if not confirm(f"Are you sure you want to delete vendor '{vname}' from this part?"):
      return

    self.part["vendor_part_numbers"] = [
      v for v in self.part.get("vendor_part_numbers", [])
      if v.get("vendor_id") != vendor_id
    ]

    try:
      anvil.server.call("save_part_from_client", self.part)
      Notification(f"🗑️ Vendor '{vname}' deleted.", style="success").show()
    except Exception as e:
      Notification(f"❌ Failed to delete vendor: {e}", style="danger").show()

    self._go_back()   # <<< use unified back

  # ---------- Navigation ----------
  def _go_back(self):
    """
    Preferred: use return_to payload if present.
    Fallbacks: PO → BOM → PartVendorRecords (your existing behavior).
    """
    if self._return_to:
      try:
        form_name = self._return_to.get("form") or "PartRecords"
        kwargs = dict(self._return_to.get("kwargs") or {})
        return_filters = self._return_to.get("filters")
        open_form(form_name, **kwargs, return_filters=return_filters)
        return
      except Exception as ex:
        Notification(f"Back navigation failed: {ex}", style="warning").show()

    if self.back_to_po:
      open_form("PurchaseOrderRecord", purchase_order_id=self.purchase_order_id)
    elif self.back_to_bom:
      open_form("DesignBOMRecord",
                assembly_part_id=self.assembly_part_id,
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status,
                prev_filter_designbom=self.prev_filter_designbom)
    else:
      open_form("PartVendorRecords",
                part_id=self.part.get("_id", ""),
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status,
                prev_filter_designbom=self.prev_filter_designbom,
                return_to=self._return_to)  # <<< propagate return path

  def button_back_click(self, **event_args):
    self._go_back()

  # ---------- Formatting helpers ----------
  def _fmt_date(self, date_input):
    if isinstance(date_input, datetime):
      return date_input.date().isoformat()
    if isinstance(date_input, date):
      return date_input.isoformat()
    if isinstance(date_input, str):
      return date_input.split("T")[0] if "T" in date_input else date_input
    return "1970-01-01"

  def _fmt_money(self, value):
    try:
      return f"${float(value):.2f}"
    except Exception:
      return "–"

  def _fmt_num(self, value):
    try:
      return f"{float(value):.2f}"
    except Exception:
      return "0.00"

  def _parse_num(self, s):
    try:
      return float((s or "").replace("$", "").replace(",", "").strip() or 0.0)
    except Exception:
      return 0.0












