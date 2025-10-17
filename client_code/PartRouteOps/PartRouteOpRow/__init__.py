from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpRowTemplate

class PartRouteOpRow(PartRouteOpRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    print("[PRORow] __init__")

  def refreshing_data_bindings(self, **event_args):
    d = dict(self.item or {})
    print("[PRORow] refreshing_data_bindings item:", d)

    # Read-only context
    self.label_seq.text  = str(d.get("seq", ""))
    self.label_cell.text = d.get("cell_name", d.get("cell_id",""))

    # Editable fields
    self.text_operation_name.text = d.get("operation_name", "")
    try:
      self.text_cycle_min.text = f"{float(d.get('cycle_min_per_unit', 0.0) or 0.0):.2f}"
    except Exception:
      self.text_cycle_min.text = "0.00"

    self.text_consumes.text  = ", ".join(d.get("consumes", []) or [])
    self.text_nc_files.text  = ", ".join(d.get("nc_files", []) or [])
    self.text_work_docs.text = ", ".join(d.get("work_docs", []) or [])

  # ---------- helpers ----------
  def _collect(self) -> dict:
    d = dict(self.item or {})
    payload = {
      "part_id":  d.get("part_id"),
      "route_id": d.get("route_id"),
      "seq":      d.get("seq"),
      "operation_name": (self.text_operation_name.text or "").strip(),
    }
    try:
      payload["cycle_min_per_unit"] = float(self.text_cycle_min.text or 0.0)
    except Exception:
      payload["cycle_min_per_unit"] = 0.0

    def _split_csv(s):
      return [t.strip() for t in (s or "").split(",") if t.strip()]

    payload["consumes"]  = _split_csv(self.text_consumes.text)
    payload["nc_files"]  = _split_csv(self.text_nc_files.text)
    payload["work_docs"] = _split_csv(self.text_work_docs.text)
    print("[PRORow] _collect ->", payload)
    return payload

  def _save(self):
    payload = self._collect()
    try:
      anvil.server.call("part_route_ops_upsert", payload)
      print("[PRORow] saved.")
      # Tell parent to refresh
      self.parent.parent.raise_event("x-row-changed")
    except Exception as e:
      print("[PRORow][ERR] save:", e)
      Notification(f"Save failed: {e}", style="danger").show()

  # ---------- autosave on blur / Enter ----------
  def text_operation_name_lost_focus(self, **e): self._save()
  def text_operation_name_pressed_enter(self, **e): self._save()

  def text_cycle_min_lost_focus(self, **e): self._save()
  def text_cycle_min_pressed_enter(self, **e): self._save()

  def text_consumes_lost_focus(self, **e): self._save()
  def text_consumes_pressed_enter(self, **e): self._save()

  def text_nc_files_lost_focus(self, **e): self._save()
  def text_nc_files_pressed_enter(self, **e): self._save()

  def text_work_docs_lost_focus(self, **e): self._save()
  def text_work_docs_pressed_enter(self, **e): self._save()

  # ---------- delete ----------
  def button_delete_row_click(self, **event_args):
    d = self.item or {}
    try:
      anvil.server.call("part_route_ops_delete",
                        d.get("part_id"), d.get("route_id"), int(d.get("seq") or 0))
      self.parent.raise_event("x-row-changed")
    except Exception as e:
      alert(f"Delete failed: {e}")




