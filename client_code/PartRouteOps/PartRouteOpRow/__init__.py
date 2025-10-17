# client_code/PartRouteOpRow/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpRowTemplate

class PartRouteOpRow(PartRouteOpRowTemplate):
  """
  One editable op row:
   - seq (TextBox), cell (DropDown)
   - operation_name, cycle_min_per_unit, consumes, nc_files, work_docs
   - Insert-below and Delete
   - Autosave on blur/Enter
  """

  def __init__(self, **properties):
    self.init_components(**properties)

  # ---------- binding ----------
  def refreshing_data_bindings(self, **event_args):
    d = dict(self.item or {})

    # Cell dropdown items & selection
    items = d.get("_cell_items") or []
    self.drop_down_cell.items = [("— select cell —","")] + items
    self.drop_down_cell.selected_value = d.get("cell_id") or ""

    # Seq (editable)
    try:
      self.text_seq.text = str(int(d.get("seq"))) if d.get("seq") is not None else ""
    except Exception:
      self.text_seq.text = ""

    # Other editable fields
    self.text_operation_name.text = d.get("operation_name", "")
    try:
      self.text_cycle_min.text = f"{float(d.get('cycle_min_per_unit', 0.0) or 0.0):.2f}"
    except Exception:
      self.text_cycle_min.text = "0.00"
    self.text_consumes.text  = ", ".join(d.get("consumes", []) or [])
    self.text_nc_files.text  = ", ".join(d.get("nc_files", []) or [])
    self.text_work_docs.text = ", ".join(d.get("work_docs", []) or [])

  # ---------- helpers ----------
  def _parent(self):
    # repeating_panel_ops -> PartRouteOps
    p = self.parent
    while p and not hasattr(p, "_on_row_changed"):
      p = getattr(p, "parent", None)
    return p

  def _collect(self) -> dict:
    d = dict(self.item or {})

    def _f(v, default=0.0):
      try:
        return float(v)
      except Exception:
        return default

    def _csv(text):
      return [t.strip() for t in (text or "").split(",") if t.strip()]

    payload = {
      "part_id":  d.get("part_id"),
      "route_id": d.get("route_id"),
      "seq":      int(self.text_seq.text or d.get("seq") or 0),
      "cell_id":  self.drop_down_cell.selected_value or None,
      "operation_name": (self.text_operation_name.text or "").strip(),
      "cycle_min_per_unit": _f(self.text_cycle_min.text or 0.0, 0.0),
      "consumes":  _csv(self.text_consumes.text),
      "nc_files":  _csv(self.text_nc_files.text),
      "work_docs": _csv(self.text_work_docs.text),
    }
    return payload

  def _save(self):
    payload = self._collect()
    if not payload.get("seq"):
      Notification("Seq is required.", style="warning").show()
      return
    try:
      anvil.server.call("part_route_ops_upsert", payload)
      p = self._parent()
      if p:
        p.raise_event("x-row-changed")
    except Exception as e:
      Notification(f"Save failed: {e}", style="danger").show()

  # ---------- autosave handlers ----------
  def text_seq_lost_focus(self, **e): self._save()
  def text_seq_pressed_enter(self, **e): self._save()

  def drop_down_cell_change(self, **e): self._save()

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

  # ---------- insert / delete ----------
  def button_insert_below_click(self, **event_args):
    d = dict(self.item or {})
    try:
      cur_seq = int(self.text_seq.text or d.get("seq") or 10)
    except Exception:
      cur_seq = 10
    new_seq = cur_seq + 1  # adjust to +5 / +10 if you want spacing
    new_cell = self.drop_down_cell.selected_value or (d.get("cell_id") or "")

    payload = {
      "part_id": d.get("part_id"),
      "route_id": d.get("route_id"),
      "seq": new_seq,
      "cell_id": new_cell or None,
      "operation_name": "",
      "cycle_min_per_unit": 0.0,
      "consumes": [],
      "nc_files": [],
      "work_docs": [],
    }
    try:
      anvil.server.call("part_route_ops_upsert", payload)
      p = self._parent()
      if p:
        p.raise_event("x-row-changed")
    except Exception as e:
      Notification(f"Insert failed: {e}", style="danger").show()

  def button_delete_row_click(self, **event_args):
    d = dict(self.item or {})
    try:
      anvil.server.call("part_route_ops_delete", d.get("part_id"), d.get("route_id"), int(d.get("seq") or 0))
      p = self._parent()
      if p:
        p.raise_event("x-row-changed")
    except Exception as e:
      Notification(f"Delete failed: {e}", style="danger").show()







