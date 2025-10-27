from anvil import *
import anvil.server
from ._anvil_designer import PBOMTemplateListTemplate

class PBOMTemplateList(PBOMTemplateListTemplate):
  def __init__(self,
               filter_parent_prefix="",
               filter_status="",
               filter_rev="",
               filter_plant="",
               **kwargs):
    self.init_components(**kwargs)

    # Button roles
    self.button_home.role = "mydefault-button"
    self.button_new_pbom.role = "new-button"
  
    # Force the exact row template (use the full dotted name shown in App Browser)
    #self.repeating_panel_pbomtpl.item_template = "PBOMTemplateList.PBOMTemplateListRow"

    # Persisted filter state
    self.prev_filter_parent_prefix = filter_parent_prefix or ""
    self.prev_filter_status = filter_status or ""
    self.prev_filter_rev = filter_rev or ""
    self.prev_filter_plant = filter_plant or ""

    # Initialise controls
    self.text_parent_prefix.text = self.prev_filter_parent_prefix
    self.drop_down_status.items = ["", "draft", "active", "obsolete", "archived"]
    self.drop_down_status.selected_value = self.prev_filter_status
    self.text_rev.text = self.prev_filter_rev
    self.text_plant.text = self.prev_filter_plant

    # Filter events
    self.text_parent_prefix.set_event_handler("pressed_enter", self.update_filter)
    self.text_rev.set_event_handler("pressed_enter", self.update_filter)
    self.text_plant.set_event_handler("pressed_enter", self.update_filter)
    self.drop_down_status.set_event_handler("change", self.update_filter)
    self.check_latest_only.checked = True
    self.check_latest_only.text = "Show latest revision only"
    self.check_latest_only.set_event_handler("change", self.update_filter)

    # Row -> List bubble event
    self.repeating_panel_pbomtpl.set_event_handler("x-open-detail", self.open_detail)
    self.repeating_panel_pbomtpl.set_event_handler("x-refresh-list", self.update_filter)

    self._last = None
    self.update_filter()

  # ---- Helpers ----
  def _normalize_rows(self, raw_rows):
    rows = []
    for r in (raw_rows or []):
      d = dict(r) if isinstance(r, dict) else {}
      _id = str(d.get("_id") or "")
      display_id = str(d.get("id") or _id)  # prefer human PBOM code if present
      rows.append({
        "_id": _id,
        "display_id": display_id,
        "parent_part_id": str(d.get("parent_part_id") or ""),
        "parent_desc": str(d.get("parent_desc") or ""),
        "rev": str(d.get("rev") or ""),
        "plant_id": str(d.get("plant_id") or ""),
        "variant": str(d.get("variant") or ""),
        "status": str(d.get("status") or ""),
      })
    return rows

  # ---- Filtering / Loading ----
  def update_filter(self, **event_args):
    # Cache filters
    self.prev_filter_parent_prefix = self.text_parent_prefix.text or ""
    self.prev_filter_status = self.drop_down_status.selected_value or ""
    self.prev_filter_rev = self.text_rev.text or ""
    self.prev_filter_plant = self.text_plant.text or ""

    sig = (self.prev_filter_parent_prefix,
           self.prev_filter_status,
           self.prev_filter_rev,
           self.prev_filter_plant,
           bool(getattr(self, "check_latest_only", None) and self.check_latest_only.checked))

    if sig == self._last:
      return
    self._last = sig

    try:
      raw = anvil.server.call(
        "pbomtpl_search",
        parent_prefix=self.prev_filter_parent_prefix,
        status=self.prev_filter_status,
        rev=self.prev_filter_rev,
        plant_id=self.prev_filter_plant,
        limit=300
      ) or []

      rows = self._normalize_rows(raw)
      if getattr(self, "check_latest_only", None) and self.check_latest_only.checked:
        rows = self._latest_only(rows)
      
      # Clear -> assign to force rebuild
      self.repeating_panel_pbomtpl.items = []
      self.repeating_panel_pbomtpl.items = rows
      self.label_count.text = f"{len(rows)} PBOM templates"
    except Exception as e:
      self.label_count.text = f"Error: {e}"
      self.repeating_panel_pbomtpl.items = []

  def _latest_only(self, rows):
    # Keep highest rev per parent_part_id (lexicographic)
    by_parent = {}
    for r in rows:
      p = r.get("parent_part_id","")
      cur = by_parent.get(p)
      if cur is None:
        by_parent[p] = r
      else:
        if (r.get("rev","") or "") >= (cur.get("rev","") or ""):
          by_parent[p] = r
    # Stable-ish order: by parent_part_id then rev
    return sorted(by_parent.values(), key=lambda x: (x.get("parent_part_id",""), x.get("rev","")))
    
  # ---- New PBOM ----
  def button_new_pbom_click(self, **event_args):
    open_form("PBOMTemplateRecord",
              pbom_id=None,
              parent_prefix=self.prev_filter_parent_prefix,
              status=self.prev_filter_status,
              rev=self.prev_filter_rev,
              plant=self.prev_filter_plant)

  # ---- Open Detail ----
  def open_detail(self, row, **event_args):
    print("open_detail in PBOMTemplateList called")
    if not isinstance(row, dict):
      return
    rid = row.get("_id")
    if not rid:
      Notification("Missing PBOM _id on row.").show()
      return
    open_form("PBOMTemplateRecord",
              pbom_id=rid,
              parent_prefix=self.prev_filter_parent_prefix,
              status=self.prev_filter_status,
              rev=self.prev_filter_rev,
              plant=self.prev_filter_plant)

  # ---- Navigation ----
  def button_home_click(self, **event_args):
    open_form("Nav")





