# client_code/ShortageRecords/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import ShortageRecordsTemplate
#from ..ShortageRecordsRow import ShortageRecordsRow

class ShortageRecords(ShortageRecordsTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)

    self._selected_ids = set()

    # Filters
    self.drop_down_status.items = ["", "open", "planned", "ordered", "closed"]
    self.drop_down_status.selected_value = ""
    self.drop_down_suggestion.items = ["all", "make", "buy"]
    self.drop_down_suggestion.selected_value = "all"

    # Wire filters (update-on-change)
    for tb in (self.text_part_prefix, self.text_vendor_substr):
      tb.set_event_handler('pressed_enter', self.update_filter)
      tb.set_event_handler('change',        self.update_filter)
    self.drop_down_status.set_event_handler('change',     self.update_filter)
    self.drop_down_suggestion.set_event_handler('change', self.update_filter)
    self.date_from.set_event_handler('change',            self.update_filter)
    self.date_to.set_event_handler('change',              self.update_filter)

    # Buttons
    #self.button_apply.role = "mydefault-button"
    self.button_last_7d.role = "mydefault-button"
    self.button_buy_selected.role = "new-button"
    #self.button_apply.set_event_handler('click',   self.update_filter)
    self.button_last_7d.set_event_handler('click', self._quick_last_7d)

    # Master checkbox
    self.check_box_master.text = "Select All (visible)"
    self.check_box_master.checked = False
    self.check_box_master.set_event_handler('change', self._toggle_master_selection)

    # Table
    #self.repeating_panel_shortages.item_template = ShortageRecords.ShortageRecordsRow
    self.repeating_panel_shortages.set_event_handler("x-select-changed", self._row_select_changed)
    self.repeating_panel_shortages.set_event_handler("x-refresh", self.update_filter)

    # Bulk action
    self.button_buy_selected.set_event_handler('click', self._merge_vendor_buy_selected)

    # Initial
    self.update_filter()

  # ---------- helpers ----------
  def _coerce_date(self, d):
    try:
      return d.date if hasattr(d, "date") else None
    except Exception: return None

  def _quick_last_7d(self, **e):
    import datetime as _dt
    today = _dt.date.today()
    self.date_from.date = today - _dt.timedelta(days=7)
    self.date_to.date   = today
    self.update_filter()

  def _visible_ids(self):
    items = self.repeating_panel_shortages.items or []
    return {r.get("_id") for r in items if r.get("_id")}

  def _apply_selection_flags(self, rows):
    return [{**r, "_selected": (r.get("_id") in self._selected_ids)} for r in (rows or [])]

  def _sync_master_checkbox(self):
    visible = self._visible_ids()
    self.check_box_master.checked = bool(visible) and (visible <= self._selected_ids)

  # ---------- filtering ----------
  def update_filter(self, **e):
    sel = self.drop_down_suggestion.selected_value or "all"
    suggestion = None if sel in ("", "all") else sel
    try:
      rows = anvil.server.call(
        "shortages_list",
        status=(self.drop_down_status.selected_value or ""),
        suggestion=suggestion or "",
        part_prefix=(self.text_part_prefix.text or ""),
        vendor_name_substr=(self.text_vendor_substr.text or ""),
        from_date=self._coerce_date(self.date_from),
        to_date=self._coerce_date(self.date_to),
        limit=500
      ) or []
      visible_ids = {r.get("_id") for r in rows if r.get("_id")}
      self._selected_ids &= visible_ids  # keep only still-visible selections
      self.repeating_panel_shortages.items = self._apply_selection_flags(rows)
      self.label_count.text = f"{len(rows)} shortages | Selected: {len(self._selected_ids)}"
      self._sync_master_checkbox()
    except Exception as ex:
      self.repeating_panel_shortages.items = []
      self.label_count.text = f"Error: {ex}"
      self.check_box_master.checked = False

  # ---------- selection plumbing ----------
  def _row_select_changed(self, shortage_id: str, checked: bool, **e):
    if not shortage_id:
      return
    if checked:
      self._selected_ids.add(shortage_id)
    else:
      self._selected_ids.discard(shortage_id)
    # Reflect in header
    self._sync_master_checkbox()
    # Update count
    items = self.repeating_panel_shortages.items or []
    self.label_count.text = f"{len(items)} shortages | Selected: {len(self._selected_ids)}"

  def _toggle_master_selection(self, **e):
    items = self.repeating_panel_shortages.items or []
    visible_ids = self._visible_ids()
    if self.check_box_master.checked:
      # select all visible
      self._selected_ids |= visible_ids
    else:
      # clear only visible (keep off-screen selections intact)
      self._selected_ids -= visible_ids
    # Repaint flags without server roundtrip
    self.repeating_panel_shortages.items = self._apply_selection_flags(items)
    self.label_count.text = f"{len(items)} shortages | Selected: {len(self._selected_ids)}"

  # ---------- bulk BUY (merge by vendor) ----------
  def _merge_vendor_buy_selected(self, **e):
    if not self._selected_ids:
      Notification("No rows selected.", style="warning").show()
      return
    if not confirm(f"Create one PO per vendor for {len(self._selected_ids)} selected shortage(s)?"):
      return
    try:
      res = anvil.server.call("shortages_merge_buy", list(self._selected_ids)) or {}
      created = int(res.get("created", 0))
      lines = int(res.get("lines", 0))
      Notification(f"Created {created} PO(s) with {lines} line(s).", style="success").show()
      # Clear selection and refresh
      self._selected_ids.clear()
      self.update_filter()
    except Exception as ex:
      alert(f"Merge failed: {ex}")


