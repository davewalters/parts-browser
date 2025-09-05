# client_code/PartRouteOpRow/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpRowTemplate

class PartRouteOpRow(PartRouteOpRowTemplate):
  """
  self.item = {"_row": {
      part_id, route_id, seq, cell_name,
      operation_name, cycle_min_per_unit, consumes[], nc_files[], work_docs[]
  }}
  """
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_save_row.role = "save-button"
    self.button_delete_row.role = "delete-button"

  def form_show(self, **event_args):
    r = dict(self.item.get("_row") or {})
    # Read-only identifiers
    self.label_seq.text = str(r.get("seq", ""))
    self.label_cell_name.text = r.get("cell_name", "")

    # Editable per-part content
    self.text_operation_name.text = r.get("operation_name", "")
    self.text_cycle_min_per_unit.text = str(r.get("cycle_min_per_unit", 0.0))
    self.text_consumes.text = ", ".join(r.get("consumes", []))
    self.text_nc_files.text = ", ".join(r.get("nc_files", []))
    self.text_work_docs.text = ", ".join(r.get("work_docs", []))

  # ---- Helpers ----
  def _payload_from_ui(self) -> dict:
    def _to_float(v, default=0.0):
      try:
        return float(str(v).strip())
      except Exception:
        return default
    def _csv_list(v: str):
      s = (v or "").strip()
      return [t.strip() for t in s.split(",") if t.strip()] if s else []

    r = dict(self.item.get("_row") or {})
    return {
      "part_id": r.get("part_id"),
      "route_id": r.get("route_id"),
      "seq": int(r.get("seq", 0)),
      "operation_name": (self.text_operation_name.text or "").strip(),
      "cycle_min_per_unit": _to_float(self.text_cycle_min_per_unit.text, 0.0),
      "consumes": _csv_list(self.text_consumes.text),
      "nc_files": _csv_list(self.text_nc_files.text),
      "work_docs": _csv_list(self.text_work_docs.text),
    }

  # ---- Events ----
  def button_save_row_click(self, **event_args):
    payload = self._payload_from_ui()
    anvil.server.call("part_route_ops_upsert", payload)
    Notification("Saved.", style="success").show()
    # Tell parent to reload (Project Pattern Log: auto-refresh on change)
    self.parent.raise_event("x-row-changed")

  def button_delete_row_click(self, **event_args):
    r = dict(self.item.get("_row") or {})
    if not confirm(f"Delete operation content for seq {r.get('seq')}?"):
      return
    ok = anvil.server.call("part_route_ops_delete", r.get("part_id"), r.get("route_id"), int(r.get("seq", 0)))
    if ok:
      Notification("Deleted.", style="info").show()
      # Tell parent to reload to show cleared state
      self.parent.raise_event("x-row-changed")

