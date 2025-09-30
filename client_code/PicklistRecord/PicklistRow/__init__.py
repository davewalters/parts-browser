# client_code/PicklistRow/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import PicklistRowTemplate

class PicklistRow(PicklistRowTemplate):
  """
  self.item schema (from parent):
    {
      "_index": line_index,
      "_picklist_id": "PL-...",
      "part_id","desc","unit",
      "qty_required","reserved_qty","short_qty",
      "pick_status", "to_bin", "from_bin", "lot_id"
    }
  """
  def __init__(self, **properties):
    self.init_components(**properties)
    self.drop_down_pick_status.items = ["pending", "picked", "partial", "out-of-stock"]
    self.drop_down_pick_status.set_event_handler("change", self._on_status_change)
    self.button_status_journal.set_event_handler("click", self._open_status_journal)
    self.button_bins_journal.set_event_handler("click", self._open_bins_journal)

  def form_show(self, **event_args):
    r = dict(self.item or {})
    self.label_part_id.text = r.get("part_id","")
    self.label_desc.text = r.get("desc","")
    self.label_unit.text = r.get("unit","")
    self.label_qty_required.text = str(r.get("qty_required",0))
    self.label_reserved_qty.text = str(r.get("reserved_qty",0))
    self.label_short_qty.text = str(r.get("short_qty",0))
    self.label_to_bin.text = r.get("to_bin","")
    self.label_from_bin.text = r.get("from_bin","")
    self.label_lot_id.text = r.get("lot_id","")
    self.drop_down_pick_status.selected_value = r.get("pick_status","pending")

  def _on_status_change(self, **event_args):
    r = dict(self.item or {})
    pid = r.get("_picklist_id")
    idx = int(r.get("_index", -1))
    new_status = self.drop_down_pick_status.selected_value
    if not pid or idx < 0:
      return
    try:
      anvil.server.call("picklist_update_line_status", pid, idx, new_status)
      # Ask parent to refresh; keeps things in sync if other totals change
      self.parent.raise_event("x-line-updated")
    except Exception as ex:
      alert(f"Update failed: {ex}")

  def _open_status_journal(self, **e):
    pid = (self.item or {}).get("part_id")
    if not pid:
      Notification("No part_id on this line.", style="warning").show(); return
    try:
      from ..InventoryStatusJournal import InventoryStatusJournal
      open_form("InventoryStatusJournal", part_id=pid)
    except Exception as ex:
      alert(f"Open Status Journal failed: {ex}")

  def _open_bins_journal(self, **e):
    pid = (self.item or {}).get("part_id")
    if not pid:
      Notification("No part_id on this line.", style="warning").show(); return
    try:
      from ..InventoryBinsJournal import InventoryBinsJournal
      open_form("InventoryBinsJournal", part_id=pid)
    except Exception as ex:
      alert(f"Open Bins Journal failed: {ex}")
