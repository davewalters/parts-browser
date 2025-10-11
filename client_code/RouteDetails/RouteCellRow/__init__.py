from anvil import *
import anvil.server
from ._anvil_designer import RouteCellRowTemplate

class RouteCellRow(RouteCellRowTemplate):
  """
  A single editable routing-step row.

  Expects self.item with:
    {
      "seq": int|None,
      "cell_id": str|"",
      "cell_name": str|"",
      "_is_blank": bool,
      "_cell_items": [(name, cell_id), ...],
      "_route_id": str
    }

  Parent (RouteDetails) listens for "x-row-changed" on the repeating panel and reloads.
  """

  def __init__(self, **properties):
    self.init_components(**properties)
    # Wire events explicitly
    self.text_seq.set_event_handler("pressed_enter", self._on_seq_commit)
    self.text_seq.set_event_handler("lost_focus",    self._on_seq_commit)
    self.drop_down_cell.set_event_handler("change",  self._on_cell_change)

    # Cache state we fill in during binding
    self._is_blank = False
    self._index    = None
    self._route_id = None

  # Called by Anvil whenever data bindings refresh (safe to rely on here)
  def refreshing_data_bindings(self, **event_args):
    d = dict(self.item or {})
    self._is_blank = bool(d.get("_is_blank"))
    self._route_id = d.get("_route_id") or None

    # Resolve our row index within the repeating panel (if available)
    try:
      self._index = list(self.parent.items or []).index(self.item)
    except Exception:
      self._index = None

    # Dropdown items
    raw_items = d.get("_cell_items") or []
    items_for_dd = []
    for it in raw_items:
      if isinstance(it, (list, tuple)) and len(it) >= 2:
        items_for_dd.append((str(it[0] or ""), str(it[1] or "")))
      elif isinstance(it, dict):
        items_for_dd.append((str(it.get("name","")), str(it.get("cell_id",""))))
    if self._is_blank:
      items_for_dd = [("— select cell —", "")] + items_for_dd
    self.drop_down_cell.items = items_for_dd

    # Selected value
    sel = "" if self._is_blank else (d.get("cell_id") or "")
    self.drop_down_cell.selected_value = sel

    # Seq text
    seq = d.get("seq")
    self.text_seq.text = "" if self._is_blank else (str(seq) if seq is not None else "")

    # Delete visible only for non-sentinel rows
    self.button_delete.visible = not self._is_blank

  # ---------- helpers ----------
  def _int_or_none(self, v):
    try:
      return int(v) if (v is not None and str(v).strip() != "") else None
    except Exception:
      return None

  def _current_inputs(self):
    seq_val = self._int_or_none(self.text_seq.text)
    cell_id = (self.drop_down_cell.selected_value or "").strip()
    return seq_val, cell_id

  def _create_if_ready(self):
    """If this is the sentinel row and both inputs exist, create the step."""
    if not self._is_blank or not self._route_id:
      return
    seq_val, cell_id = self._current_inputs()
    if (seq_val is not None) and cell_id:
      anvil.server.call("routes_add_cell", self._route_id, {"seq": int(seq_val), "cell_id": cell_id})
      # Tell parent to reload & append a new sentinel
      self.parent.raise_event("x-row-changed")

  def _update_existing(self, patch: dict):
    if not patch or self._index is None or self._route_id is None:
      return
    anvil.server.call("routes_update_cell", self._route_id, int(self._index), patch)
    self.parent.raise_event("x-row-changed")

  # ---------- events ----------
  def _on_seq_commit(self, **e):
    if self._is_blank:
      self._create_if_ready()
    else:
      val = self._int_or_none(self.text_seq.text)
      if val is None:
        Notification("Seq must be an integer").show()
        # Ask parent to reload to restore correct value
        self.parent.raise_event("x-row-changed")
        return
      self._update_existing({"seq": val})

  def _on_cell_change(self, **e):
    if self._is_blank:
      self._create_if_ready()
    else:
      cell_id = (self.drop_down_cell.selected_value or "").strip()
      if cell_id:
        self._update_existing({"cell_id": cell_id})

  def button_delete_click(self, **e):
    if self._index is None or self._route_id is None:
      return
    anvil.server.call("routes_remove_cell", self._route_id, int(self._index))
    self.parent.raise_event("x-row-changed")










  