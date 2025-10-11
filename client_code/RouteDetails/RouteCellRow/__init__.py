from ._anvil_designer import RouteCellRowTemplate
from anvil import *
import anvil.server

class RouteCellRow(RouteCellRowTemplate):
  """
  A row for editing a single routing step.
  Parent (RouteDetails) injects per-row:
    item = {
      "seq": int|None,
      "cell_id": str,
      "_is_blank": bool,
      "_cell_items": [(name, cell_id), ...]
    }
  """
  def __init__(self, **kwargs):
    self.init_components(**kwargs)
    self._route_id = None
    self._index = None
    self._is_blank = False

  # Parent calls this after items are set to force-populate the row
  def rebind(self):
    d = dict(self.item or {})
    self._is_blank = bool(d.get("_is_blank"))

    # Derive index robustly
    try:
      self._index = list(self.parent.items or []).index(self.item)
    except Exception:
      self._index = None

    # Seq
    seq = d.get("seq")
    self.text_seq.text = "" if self._is_blank else (str(seq) if seq is not None else "")

    # Dropdown items from row payload
    items = d.get("_cell_items") or []
    norm = []
    for it in items:
      if isinstance(it, (list, tuple)) and len(it) >= 2:
        norm.append((str(it[0] or ""), str(it[1] or "")))
      elif isinstance(it, dict):
        norm.append((str(it.get("name","")), str(it.get("cell_id",""))))
      else:
        s = str(it)
        norm.append((s, s))

    if self._is_blank:
      norm = [("— select cell —", "")] + norm

    self.drop_down_cell.items = norm
    self.drop_down_cell.selected_value = "" if self._is_blank else (d.get("cell_id") or "")

    # Delete button only for real rows
    self.button_delete.visible = not self._is_blank

  # ---------- helpers ----------
  def _int_or_none(self, v):
    try:
      return int(v) if (v is not None and str(v).strip() != "") else None
    except Exception:
      return None

  def _route_id_from_parent(self):
    # Walk up to RouteDetails once, cache
    if self._route_id:
      return self._route_id
    p = self.parent
    while p and not hasattr(p, "route_id"):
      p = getattr(p, "parent", None)
    self._route_id = getattr(p, "route_id", None)
    return self._route_id

  def _notify_parent_reload(self):
    p = self.parent
    while p and not hasattr(p, "on_row_changed"):
      p = getattr(p, "parent", None)
    if p:
      p.on_row_changed()

  # ---------- update-on-change ----------
  def text_seq_change(self, **e):
    val = self._int_or_none(self.text_seq.text)
    if val is None:
      Notification("Seq must be an integer").show(); return

    route_id = self._route_id_from_parent()
    if not route_id:
      Notification("Route not ready").show(); return

    if self._is_blank:
      cell_id = self.drop_down_cell.selected_value or ""
      if not cell_id:
        Notification("Select a cell first").show(); return
      anvil.server.call("routes_add_cell", route_id, {"seq": int(val), "cell_id": cell_id})
    else:
      if self._index is None: return
      anvil.server.call("routes_update_cell", route_id, self._index, {"seq": int(val)})
    self._notify_parent_reload()

  def drop_down_cell_change(self, **e):
    route_id = self._route_id_from_parent()
    if not route_id:
      Notification("Route not ready").show(); return

    cell_id = self.drop_down_cell.selected_value or ""
    if self._is_blank:
      seq_val = self._int_or_none(self.text_seq.text) or (self.item.get("seq") if self.item else 10) or 10
      if not cell_id: return
      anvil.server.call("routes_add_cell", route_id, {"seq": int(seq_val), "cell_id": cell_id})
    else:
      if self._index is None: return
      anvil.server.call("routes_update_cell", route_id, self._index, {"cell_id": cell_id})
    self._notify_parent_reload()

  def button_delete_click(self, **e):
    route_id = self._route_id_from_parent()
    if not route_id or self._index is None: return
    anvil.server.call("routes_remove_cell", route_id, self._index)
    self._notify_parent_reload()





  