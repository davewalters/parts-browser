# client_code/PicklistRecord/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import PicklistRecordTemplate
from ..PicklistRow import PicklistRow

class PicklistRecord(PicklistRecordTemplate):
  def __init__(self, picklist_id: str, **kwargs):
    self.init_components(**kwargs)
    self.picklist_id = picklist_id

    self.button_back.role = "mydefault-button"
    self.button_flag_shortages.role = "new-button"

    self.repeating_panel_lines.item_template = PicklistRow
    # child rows notify parent to refresh after status change
    self.repeating_panel_lines.set_event_handler("x-line-updated", self._reload)

    # filter
    self.drop_down_bin_filter.items = ["All"]
    self.drop_down_bin_filter.selected_value = "All"
    self.drop_down_bin_filter.set_event_handler("change", self._apply_filter)

    self._raw_doc = {}
    self._view_items = []
    self._reload()

  # -------- data loaders --------
  def _reload(self, **e):
    try:
      doc = anvil.server.call("picklist_get", self.picklist_id)  # you likely already have this
      # If you don't, add in uplink: return db.picklists.find_one({"_id": norm_id(pid)})
      if not doc:
        alert("Picklist not found."); 
        self._raw_doc = {}
        self._view_items = []
        self.repeating_panel_lines.items = []
        return

      self._raw_doc = doc

      # Header
      self.label_picklist_id.text = doc.get("_id","")
      self.label_wo_id.text = doc.get("wo_id","")
      self.label_created_ts.text = str(doc.get("created_ts",""))

      # Build view and the bin filter list
      items = []
      bin_values = set(["All"])
      for idx, ln in enumerate(doc.get("lines") or []):
        to_bin = ln.get("to_bin") or ""
        bin_values.add(to_bin or "")
        row = dict(ln)
        row["_index"] = idx
        row["_picklist_id"] = doc.get("_id")
        items.append(row)

      self._view_items = sorted(items, key=lambda r: (r.get("to_bin") or "", r.get("part_id") or ""))
      # Populate filter dropdown (keep 'All' first)
      sorted_bins = ["All"] + sorted([b for b in bin_values if b and b != "All"])
      self.drop_down_bin_filter.items = sorted_bins
      if self.drop_down_bin_filter.selected_value not in self.drop_down_bin_filter.items:
        self.drop_down_bin_filter.selected_value = "All"

      self._apply_filter()

    except Exception as ex:
      alert(f"Load failed: {ex}")

  def _apply_filter(self, **e):
    sel = self.drop_down_bin_filter.selected_value or "All"
    if sel == "All":
      self.repeating_panel_lines.items = self._view_items
    else:
      self.repeating_panel_lines.items = [r for r in self._view_items if (r.get("to_bin") or "") == sel]

  # -------- actions --------
  def button_flag_shortages_click(self, **event_args):
    try:
      res = anvil.server.call("picklist_flag_shortages", self.picklist_id) or {}
      Notification(f"Flagged shortages: {int(res.get('count',0))}", style="info").show()
    except Exception as ex:
      alert(f"Flagging shortages failed: {ex}")

  def button_back_click(self, **event_args):
    try:
      from ..WorkOrderRecord import WorkOrderRecord
      open_form("WorkOrderRecord", wo_id=self.label_wo_id.text)
    except Exception:
      open_form("Nav")
opens.
