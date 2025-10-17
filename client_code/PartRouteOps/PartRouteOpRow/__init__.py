from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpRowTemplate

class PartRouteOpRow(PartRouteOpRowTemplate):
  """
  One editable operation row for a given route step (seq, cell).
  Saves via upsert on blur/Enter; delete clears the override for this seq.
  """

  def __init__(self, **properties):
    self.init_components(**properties)

    # Optional roles
    try:
      self.button_delete.role = "delete-button"
    except Exception:
      pass

  # Anvil calls this when item changes or needs rebinding
  def refreshing_data_bindings(self, **event_args):
    d = self.item or {}

    # Display-only columns
    self.label_seq.text       = str(d.get("seq", ""))
    self.label_cell_name.text = d.get("cell_name", "")

    # Editable fields
    self.text_operation_name.text = d.get("operation_name", "")
    try:
      self.text_cycle_min_per_unit.text = f"{float(d.get('cycle_min_per_unit', 0.0)):.3f}"
    except Exception:
      self.text_cycle_min_per_unit.text = "0.000"

    # Delete visible only when we actually have an override doc
    self.button_delete.visible = bool(d.get("_has_op", False))

  # ---------- save helpers ----------
  def _collect_payload(self) -> dict:
    d = self.item or {}
    # Coerce number
    try:
      cycle = float(self.text_cycle_min_per_unit.text or 0.0)
    except Exception:
      cycle = 0.0
    return {
      "part_id": str(d.get("part_id") or ""),
      "route_id": str(d.get("route_id") or ""),
      "seq": int(d.get("seq") or 0),
      "operation_name": (self.text_operation_name.text or "").strip(),
      "cycle_min_per_unit": cycle,
      # Keep existing lists unless you add editors for them
      "consumes": list(d.get("consumes") or []),
      "nc_files": list(d.get("nc_files") or []),
      "work_docs": list(d.get("work_docs") or []),
    }

  def _save(self):
    payload = self._collect_payload()
    if not payload["part_id"] or not payload["route_id"] or payload["seq"] <= 0:
      Notification("Row is missing identifiers; cannot save.", style="warning").show()
      return
    try:
      anvil.server.call("part_route_ops_upsert", payload)
      # Tell parent we changed, so it can refresh rows (and toggle delete visibility etc.)
      self.parent.raise_event("x-row-changed")
    except Exception as e:
      alert(f"Save failed: {e}")

  # ---------- events: save on blur / Enter ----------
  def text_operation_name_lost_focus(self, **event_args):
    self._save()

  def text_operation_name_pressed_enter(self, **event_args):
    self._save()

  def text_cycle_min_per_unit_lost_focus(self, **event_args):
    self._save()

  def text_cycle_min_per_unit_pressed_enter(self, **event_args):
    self._save()

  # ---------- delete ----------
  def button_delete_row_click(self, **event_args):
    d = self.item or {}
    try:
      anvil.server.call("part_route_ops_delete",
                        d.get("part_id"), d.get("route_id"), int(d.get("seq") or 0))
      self.parent.raise_event("x-row-changed")
    except Exception as e:
      alert(f"Delete failed: {e}")


