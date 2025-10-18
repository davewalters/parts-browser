from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpRowTemplate

class PartRouteOpRow(PartRouteOpRowTemplate):
  """
  One editable operation row for PartRouteOps:
    • seq (TextBox), cell (DropDown)
    • operation_name, cycle_min_per_unit, consumes, nc_files, work_docs
    • Insert-below and Delete
    • Autosave on blur/Enter/change -> server upsert -> parent.reload()
  Expects item with keys:
    part_id, route_id, seq, cell_id, operation_name, cycle_min_per_unit,
    consumes, nc_files, work_docs, _cell_items=[(cell_name, cell_id), ...]
  """

  def __init__(self, **properties):
    self.init_components(**properties)

  # ---------- utilities ----------
  def _parent(self):
    # Find the PartRouteOps parent that exposes reload()
    p = self.parent
    while p and not hasattr(p, "reload"):
      p = getattr(p, "parent", None)
    return p

  def _csv(self, s):
    return [t.strip() for t in (s or "").split(",") if t.strip()]

  def _as_int(self, txt, fb=0):
    try:
      return int(txt) if (txt is not None and str(txt).strip() != "") else int(fb or 0)
    except:
      return int(fb or 0)

  def _as_float(self, txt, fb=0.0):
    try:
      return float(txt)
    except:
      return float(fb)

  # ---------- binding ----------
  def refreshing_data_bindings(self, **event_args):
    d = dict(self.item or {})
    print("[PRORow] bind seq=", d.get("seq"), "cell_id=", d.get("cell_id"))

    # Cell dropdown
    items = d.get("_cell_items") or []
    print("[PRORow] cell choices sample:", items[:3] if items else "[]")
    self.drop_down_cell.items = [("— select cell —", "")] + items
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

  # ---------- collect & save ----------
  def _collect(self) -> dict:
    d = dict(self.item or {})
    seq_val = self._as_int(self.text_seq.text, d.get("seq"))

    payload = {
      "part_id":  d.get("part_id"),
      "route_id": d.get("route_id"),
      "seq":      seq_val,
      "cell_id":  (self.drop_down_cell.selected_value or "") or None,
      "operation_name": (self.text_operation_name.text or "").strip(),
      "cycle_min_per_unit": self._as_float(self.text_cycle_min.text or 0.0, 0.0),
      "consumes":  self._csv(self.text_consumes.text),
      "nc_files":  self._csv(self.text_nc_files.text),
      "work_docs": self._csv(self.text_work_docs.text),
    }
    print("[PRORow] _collect ->", payload)
    return payload

  def _save_then_reload(self):
    payload = self._collect()
    if not payload.get("seq"):
      Notification("Seq is required.", style="warning").show()
      return
    try:
      anvil.server.call("part_route_ops_upsert", payload)
      print("[PRORow] saved.")
      p = self._parent()
      if p:
        p.reload()
    except Exception as e:
      print("[PRORow][ERR] save:", e)
      Notification(f"Save failed: {e}", style="danger").show()

  # ---------- autosave handlers ----------
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

  # ---------- insert / delete ----------
  def button_insert_below_click(self, **event_args):
    d = dict(self.item or {})
    # Choose new seq = current + 1 (simple, deterministic)
    cur_seq = self._as_int(self.text_seq.text, d.get("seq"))
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
    print("[PRORow] insert payload ->", payload)
    try:
      anvil.server.call("part_route_ops_upsert", payload)
      p = self._parent()
      if p:
        p.reload()
    except Exception as e:
      print("[PRORow][ERR] insert:", e)
      alert(f"Insert failed: {e}")

  def button_delete_row_click(self, **event_args):
    if not confirm("Delete this operation step?"):
      return
    d = dict(self.item or {})
    try:
      anvil.server.call("part_route_ops_delete",
                        d.get("part_id"), d.get("route_id"), int(d.get("seq") or 0))
      p = self._parent()
      if p:
        p.reload()
    except Exception as e:
      print("[PRORow][ERR] delete:", e)
      Notification(f"Delete failed: {e}", style="danger").show()










