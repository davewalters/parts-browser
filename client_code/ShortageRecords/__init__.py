# client_code/ShortageRecords/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import ShortageRecordsTemplate
from ..ShortageRecordsRow import ShortageRecordsRow

class ShortageRecords(ShortageRecordsTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)

    # Filters
    self.drop_down_status.items = ["", "open", "planned", "ordered", "closed"]
    self.drop_down_status.selected_value = ""
    self.drop_down_suggestion.items = ["", "make", "buy"]
    self.drop_down_suggestion.selected_value = ""

    # Events: update-on-change
    for tb in (self.text_part_prefix, self.text_vendor_substr):
      tb.set_event_handler('pressed_enter', self.update_filter)
      tb.set_event_handler('change', self.update_filter)
    self.drop_down_status.set_event_handler('change', self.update_filter)
    self.drop_down_suggestion.set_event_handler('change', self.update_filter)
    self.date_from.set_event_handler('change', self.update_filter)
    self.date_to.set_event_handler('change', self.update_filter)

    self.button_apply.role = "mydefault-button"
    self.button_last_7d.role = "mydefault-button"
    self.button_apply.set_event_handler('click', self.update_filter)
    self.button_last_7d.set_event_handler('click', self._quick_last_7d)

    # Repeating panel
    self.repeating_panel_shortages.item_template = ShortageRecordsRow
    self.repeating_panel_shortages.set_event_handler("x-refresh", self.update_filter)

    # But all shortages in filter set and merge by vendor
    self.button_merge_vendor_buy.role = "save-button"
    self.button_merge_vendor_buy.set_event_handler('click', self._merge_vendor_buy)
    
    # Initial
    self.update_filter()

  def _coerce_date(self, d):
    try: return d.date if hasattr(d, "date") else None
    except Exception: return None

  def _quick_last_7d(self, **e):
    import datetime as _dt
    today = _dt.date.today()
    self.date_from.date = today - _dt.timedelta(days=7)
    self.date_to.date = today
    self.update_filter()

  def _current_visible_ids(self) -> list:
    # repeating_panel_shortages.items holds the filtered, visible rows
    try:
      return [r.get("_id") for r in (self.repeating_panel_shortages.items or []) if r.get("_id")]
    except Exception:
      return []

  def _merge_vendor_buy(self, **event_args):
    # Optional: warn if the set contains any non-buy or open_short_qty==0 rows — server filters anyway
    ids = self._current_visible_ids()
    if not ids:
      Notification("No rows to merge.", style="warning").show(); return
    if not confirm(f"Create one PO per vendor for {len(ids)} visible shortage(s)?"):
      return
    try:
      res = anvil.server.call("shortages_merge_buy", ids) or {}
      created = int(res.get("created", 0))
      lines = int(res.get("lines", 0))
      Notification(f"Created {created} PO(s) with {lines} line(s).", style="success").show()
      self.update_filter()
    except Exception as ex:
      alert(f"Merge failed: {ex}")

  def update_filter(self, **e):
    try:
      rows = anvil.server.call(
        "shortages_list",
        status=(self.drop_down_status.selected_value or ""),
        suggestion=(self.drop_down_suggestion.selected_value or ""),
        part_prefix=(self.text_part_prefix.text or ""),
        vendor_name_substr=(self.text_vendor_substr.text or ""),
        from_date=self._coerce_date(self.date_from),
        to_date=self._coerce_date(self.date_to),
        limit=500
      ) or []
      self.repeating_panel_shortages.items = rows
      self.label_count.text = f"{len(rows)} shortages"
    except Exception as ex:
      self.repeating_panel_shortages.items = []
      self.label_count.text = f"Error: {ex}"

