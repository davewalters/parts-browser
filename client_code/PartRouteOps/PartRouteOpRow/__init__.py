# client_code/PartRouteOpRow/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpRowTemplate

class PartRouteOpRow(PartRouteOpRowTemplate):
  """
  Row:
    • seq TextBox, cell DropDown
    • operation_name, cycle_min_per_unit, consumes, nc_files, work_docs
    • Insert-below and Delete buttons
    • On blur/Enter/change: save to server, then parent.reload()
  """

  def __init__(self, **properties):
    self.init_components(**properties)

  # Utility to find parent.reload()
  def _parent(self):
    p = self.parent
    while p and not hasattr(p, "reload"):
      p = getattr(p, "parent", None)
    return p

  # Bind from item (no local caching)
  def refreshing_data_bindings(self, **event_args):
    d = dict(self.item or {})

    # Cells
    items = d.get("_cell_items") or []
    self.drop_down_cell.items = [("— select cell —", "")] + items
    self.drop_down_cell.selected_value = d.get("cell_id") or ""

    # Seq
    try:
      self.text_seq.text = str(int(d.get("seq"))) if d.get("seq") is not None else ""
    except:
      self.text_seq.text = ""

    # Other editable fields
    self.text_operation_name.text = d.get("operation_name", "")
    try:
      self.text_cycle_min.text = f"{float(d.get('cycle_min_per_unit', 0.0) or 0.0):.2f}"
    except:
      self.text_cycle_min.text = "0.00"

    self.text_consumes.text  = ", ".join(d.get("consumes", []) or [])
    self.text_nc_files.text  = ", ".join(d.get("nc_files", []) or [])
    self.text_work_docs.text = ", ".join(d.get("work_docs", []) or [])

  # Collect payload for server
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

    def _csv(s):
      return [t.strip() for t in (s or "").split(",") if t.strip()]

    seq_val = _as_int(self.text_seq.text, d.get("seq"))
    return {
      "part_id":  d.get("part_id"),
      "route_id": d.get("route_id"),
      "seq":      seq_val,
      "cell_id":  (self.drop_down_cell.selected_value or "") or None,
      "operation_name": (self.text_operation_name.text or "").strip(),
      "cycle_min_per_unit": _as_float(self.text_cycle_min.text or 0.0, 0.0),
      "consumes":  _csv(self.text_consumes.text),
      "nc_files":  _csv(self.text_nc_files.text),
      "work_docs": _csv(self.text_work_docs.text),
    }

  def _save_then_reload(self):
    payload = self._collect()
    if not payload.get("seq"):
      Notification("Seq is required.", style="warning").show()
      return
    try:
      anvil.server.call("part_route_ops_upsert", payload)
      p = self._parent()
      if p: p.reload()
    except Exception as e:
      Notification(f"Save failed: {e}", style="danger").show()

  # Autosave on blur / Enter / change
  def text_seq_lost_focus(self, **e): self._save_then_reload()
  def text_seq_pressed_enter(self, **e): self._save_then_reload()

  def drop_down_cell_change(self, **e): self._save_then_reload()

  def text_operation_name_lost_focus(self, **e): self._save_then_reload()
  def text_operation_name_pressed_enter(self, **e): self._save_then_reload()

  def text_cycle_min_lost_focus(self, **e): self._save_then_reload()
  def text_cycle_min_pressed_enter(self, **e): self._save_then_reload()

  def text_consumes_lost_focus(self, **e): self._save_then_reload()
  def text_consumes_pressed_enter(self, **e): self._save_then_reload()

  def text_nc_files_lost_focus(self, **e): self._save_then_reload()
  def text_nc_files_pressed_enter(self, **e): self._save_then_reload()

  def text_work_docs_lost_focus(self, **e): self._save_then_reload()
  def text_work_docs_pressed_enter(self, **e): self._save_then_reload()

  # Insert and Delete
  def button_insert_below_click(self, **event_args):
    d = dict(self.item or {})
    items = list(self.parent.items or [])
    try:
      idx = items.index(self.item)
    except Exception:
      idx = -1

    try:
      cur_seq = int(self.text_seq.text) if (self.text_seq.text or "").strip() else int(d.get("seq") or 0)
    except:
      cur_seq = int(d.get("seq") or 0)

    # choose a nice middle if possible, else +10
    #new_seq = cur_seq + 10
    #if 0 <= idx < len(items) - 1:
    #  try:
    #    nxt_seq = int(items[idx+1].get("seq") or 0)
    #    gap = nxt_seq - cur_seq
    #    if gap >= 2:
    #      new_seq = cur_seq + gap // 2
    #  except:
    #    pass
    new_seq = cur_seq + 1

    payload = {
      "part_id": d.get("part_id"),
      "route_id": d.get("route_id"),
      "seq": int(new_seq),
      "cell_id": (self.drop_down_cell.selected_value or "") or None,
      "operation_name": "",
      "cycle_min_per_unit": 0.0,
      "consumes": [],
      "nc_files": [],
      "work_docs": [],
    }
    try:
      anvil.server.call("part_route_ops_upsert", payload)
      p = self._parent()
      if p: p.reload()
    except Exception as e:
      alert(f"Insert failed: {e}")

  def button_delete_row_click(self, **event_args):
    if not confirm("Delete this operation step?"):
      return
    d = dict(self.item or {})
    try:
      anvil.server.call("part_route_ops_delete", d.get("part_id"), d.get("route_id"), int(d.get("seq") or 0))
      p = self._parent()
      if p: p.reload()
    except Exception as e:
      Notification(f"Delete failed: {e}", style="danger").show()









