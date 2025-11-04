from anvil import *
import anvil.server
# from anvil.js.window import setTimeout   # <- not needed; avoid timers

from ._anvil_designer import PartRecordsTemplate
from .. import config

class PartRecords(PartRecordsTemplate):
  def __init__(self,
               filter_part="",
               filter_desc="",
               filter_type="",
               filter_status="",
               filter_designbom=False,
               return_filters: dict | None = None,
               **kwargs):
    self.init_components(**kwargs)

    # Preserve previous filters (legacy path)
    self.prev_filter_part = filter_part
    self.prev_filter_desc = filter_desc
    self.prev_filter_type = filter_type
    self.prev_filter_status = filter_status
    self.prev_filter_designbom = filter_designbom

    self.button_new_part.role = "new-button"
    self.button_home.role = "mydefault-button"
    self.repeating_panel_1.role = "scrolling-panel"

    # Configure dropdown items
    self.drop_down_type.items = [""] + ["part", "assembly", "phantom", "material", "service", "documentation"]
    self.drop_down_status.items = [""] + ["active", "obsolete"]

    # If return_filters provided, it overrides the legacy args
    if return_filters:
      self._apply_filter_dict(return_filters)
    else:
      # Legacy: set from positional args
      self.text_box_part_no.text = filter_part
      self.text_box_desc.text = filter_desc
      self.drop_down_type.selected_value = filter_type
      self.drop_down_status.selected_value = filter_status
      self.check_box_designbom.checked = filter_designbom

    # Wire events
    self.text_box_part_no.set_event_handler('pressed_enter', self.update_filter)
    self.text_box_desc.set_event_handler('pressed_enter', self.update_filter)
    self.drop_down_type.set_event_handler('change', self.update_filter)
    self.drop_down_status.set_event_handler('change', self.update_filter)
    self.check_box_designbom.set_event_handler('change', self.update_filter)
    self.repeating_panel_1.set_event_handler("x-show-detail", self.show_detail)

    # Initial load
    self.update_filter()

  # ---- New helper: filter dict <-> widgets ----
  def current_filters(self) -> dict:
    return {
      "part": self.text_box_part_no.text or "",
      "desc": self.text_box_desc.text or "",
      "type": self.drop_down_type.selected_value or "",
      "status": self.drop_down_status.selected_value or "",
      "designbom": bool(self.check_box_designbom.checked),
    }

  def _apply_filter_dict(self, f: dict):
    self.text_box_part_no.text = f.get("part", "")
    self.text_box_desc.text = f.get("desc", "")
    self.drop_down_type.selected_value = f.get("type", "")
    self.drop_down_status.selected_value = f.get("status", "")
    self.check_box_designbom.checked = bool(f.get("designbom", False))

    # Keep legacy prev_* in sync (for any callers still using them)
    self.prev_filter_part = self.text_box_part_no.text or ""
    self.prev_filter_desc = self.text_box_desc.text or ""
    self.prev_filter_type = self.drop_down_type.selected_value or ""
    self.prev_filter_status = self.drop_down_status.selected_value or ""
    self.prev_filter_designbom = self.check_box_designbom.checked

  # ---- Existing logic ----
  def update_filter(self, **event_args):
    # Sync legacy prev_* fields (still used elsewhere)
    cf = self.current_filters()
    self.prev_filter_part = cf["part"]
    self.prev_filter_desc = cf["desc"]
    self.prev_filter_type = cf["type"]
    self.prev_filter_status = cf["status"]
    self.prev_filter_designbom = cf["designbom"]

    try:
      results = anvil.server.call(
        "get_filtered_parts",
        prefix=self.prev_filter_part,
        desc=self.prev_filter_desc,
        part_type=self.prev_filter_type,
        status=self.prev_filter_status,
        designbom=self.prev_filter_designbom,
      )

      vendor_ids = sorted({ r.get("default_vendor") for r in results if r.get("default_vendor") })
      try:
        name_map = anvil.server.call("get_vendor_names_by_ids", vendor_ids) or {}
      except Exception:
        name_map = {}

      name_map = { str(k): (v if isinstance(v, str) and v.strip() else str(k)) for k, v in name_map.items() }

      annotated = []
      for r in results:
        vid = str(r.get("default_vendor") or "")
        r2 = dict(r)
        r2["_vendor_name"] = name_map.get(vid, vid)
        annotated.append(r2)

      self.repeating_panel_1.items = annotated
      self.label_count.text = f"{len(annotated)} parts returned"

    except Exception as e:
      self.label_count.text = f"Error: {e}"
      self.repeating_panel_1.items = []

  def show_detail(self, part, **event_args):
    try:
      part_id = part["_id"]
      # Single payload with return form + filters
      return_to = {
        "form": "PartRecords",
        "kwargs": {},  # no ctor args needed for list; we’ll use return_filters below
        "filters": self.current_filters(),
      }
      open_form("PartRecord", part_id=part_id, return_to=return_to)
    except Exception as e:
      alert(f"Error loading part detail: {e}")

  def button_new_part_click(self, **event_args):
    return_to = {
      "form": "PartRecords",
      "kwargs": {},
      "filters": self.current_filters(),
    }
    open_form("PartRecord", part_id=None, return_to=return_to)

  def button_home_click(self, **event_args):
    open_form("Nav")


  







