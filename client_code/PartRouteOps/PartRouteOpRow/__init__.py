from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpRowTemplate

class PartRouteOpRow(PartRouteOpRowTemplate):
  """
  One editable op row:
   - seq (TextBox), cell (DropDown)
   - operation_name, cycle_min_per_unit, consumes, nc_files, work_docs
   - Insert-below and Delete
   - Autosave on blur/Enter/change -> server -> parent.reload()
  """

  def __init__(self, **properties):
    super().__init__(**properties)

    # Wire all handlers HERE (ignore Designer bindings)
    self.text_seq.set_event_handler("lost_focus", self._save_then_reload)
    self.text_seq.set_event_handler("pressed_enter", self._save_then_reload)

    self.drop_down_cell.set_event_handler("change", self._save_then_reload)

    self.text_operation_name.set_event_handler("lost_focus", self._save_then_reload)
    self.text_operation_name.set_event_handler("pressed_enter", self._save_then_reload)

    self.text_cycle_min.set_event_handler("lost_focus", self._save_then_reload)
    self.text_cycle_min.set_event_handler("pressed_enter", self._save_then_reload)

    self.text_consumes.set_event_handler("lost_focus", self._save_then_reload)
    self.text_consumes.set_event_handler("pressed_enter", self._save_then_reload)

    self.text_nc_files.set_event_handler("lost_focus", self._save_then_reload)
    self.text_nc_files.set_event_handler("pressed_enter", self._save_then_reload)

    self.text_work_docs.set_event_handler("lost_focus", self._save_then_reload)
    self.text_work_docs.set_event_handler("pressed_enter", self._save_then_reload)

    #self.button_insert_below.set_event_handler("click", self._insert_below)
    #self.button_delete_row.set_event_handler("click", self._delete_row)

  # Called by parent after it assigns items; safe to call anytime
  def _bind_from_item(self):
    d = dict(self.item or {})

    # Dropdown items & selection (prepend placeholder)
    items = d.get("_cell_items") or []
    self.drop_down_cell.items = [("— select cell —","")] + items
    self.drop_down_cell.selected_value = d.get("cell_id") or ""

    # Seq
    seq = d.get("seq")
    self.text_seq.text = "" if seq is None else str(int(seq))

    # Other fields
    self.text_operation_name.text = d.get("operation_name", "")
    try:
      self.text_cycle_min.text = f"{float(d.get('cycle_min_per_unit', 0.0) or 0.0):.2f}"
    except Exception:
      self.text_cycle_min.text = "0.00"

    self.text_consumes.text  = ", ".join(d.get("consumes", []) or [])
    self.text_nc_files.text  = ", ".join(d.get("nc_files", []) or [])
    self.text_work_docs.text = ", ".join(d.get("work_docs", []) or [])

  # Utilities
  def _parent(self):
    p = self.parent
    while p and not hasattr(p, "reload"):
      p = getattr(p, "parent", None)
    return p

  def _csv(self, s):
    return [t.strip() for t in (s or "").split(",") if t.strip()]

  def _collect(self) -> dict:
    d = dict(self.item or {})

    def _as_int(txt, fb):
      try:
        return int(txt) if (txt is not None and str(txt).strip() != "") else int(fb or 0)
      except:
        return int(fb or 0)

    def _as_float(txt, fb=0.0):
      try:
        return float(txt)
      except:
        return float(fb)

    seq_val = _as_int(self.text_seq.text, d.get("seq"))
    return {
      "part_id":  d.get("part_id"),
      "route_id": d.get("route_id"),
      "seq":      seq_val,
      "cell_id":  (self.drop_down_cell.selected_value or "") or None,
      "operation_name": (self.text_operation_name.text or "").strip(),
      "cycle_min_per_unit": _as_float(self.text_cycle_min.text or 0.0, 0.0),
      "consumes":  self._csv(self.text_consumes.text),
      "nc_files":  self._csv(self.text_nc_files.text),
      "work_docs": self._csv(self.text_work_docs.text),
    }

  def _save_then_reload(self, **event_args):
    payload = self._collect()
    if not payload.get("seq"):
      Notification("Seq is required.", style="warning").show()
      return
    try:
      anvil.server.call("part_route_ops_upsert", payload)
      p = self._parent()
      if p: p.raise_event("x-row-changed")
    except Exception as e:
      Notification(f"Save failed: {e}", style="danger").show()

  # Insert / Delete
  def button_insert_below_click(self, **event_args):
    d = dict(self.item or {})
    try:
      cur_seq = int(self.text_seq.text or d.get("seq") or 0)
    except:
      cur_seq = int(d.get("seq") or 0)

    new_seq = cur_seq + 1
    payload = {
      "part_id":  d.get("part_id"),
      "route_id": d.get("route_id"),
      "seq":      int(new_seq),
      "cell_id":  (self.drop_down_cell.selected_value or "") or None,
      "operation_name": "",
      "cycle_min_per_unit": 0.0,
      "consumes": [],
      "nc_files": [],
      "work_docs": [],
    }
    try:
      anvil.server.call("part_route_ops_upsert", payload)
      p = self._parent()
      if p: p.raise_event("x-row-changed")
    except Exception as e:
      alert(f"Insert failed: {e}")

  def button_delete_row_click(self, **event_args):
    if not confirm("Delete this operation step?"):
      return
    d = dict(self.item or {})
    try:
      anvil.server.call("part_route_ops_delete",
                        d.get("part_id"), d.get("route_id"), int(d.get("seq") or 0))
      p = self._parent()
      if p: p.raise_event("x-row-changed")
    except Exception as e:
      Notification(f"Delete failed: {e}", style="danger").show()

 












