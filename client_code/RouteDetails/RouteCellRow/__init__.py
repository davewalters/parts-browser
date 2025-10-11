from ._anvil_designer import RouteCellRowTemplate
from anvil import *
import anvil.server

class RouteCellRow(RouteCellRowTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)
    self._parent   = self._find_route_details_parent()
    self._route_id = getattr(self._parent, "route_id", None)
    self._index    = None
    self._is_blank = False

  def _find_route_details_parent(self):
    p = self.parent
    while p is not None and not hasattr(p, "on_row_changed"):
      p = getattr(p, "parent", None)
    return p

  def form_show(self, **event_args):
    d = dict(self.item or {})
    self._is_blank = bool(d.get("_is_blank"))
    try:
      self._index = list(self.parent.items or []).index(self.item)
    except Exception:
      self._index = None

    # Normalize dropdown items to list[(text,value)]
    raw_items = d.get("_cell_items") or []
    items_for_dd = []
    for it in raw_items:
      if isinstance(it, (list, tuple)) and len(it) >= 2:
        items_for_dd.append((str(it[0] or ""), str(it[1] or "")))
      elif isinstance(it, dict):
        items_for_dd.append((str(it.get("name","")), str(it.get("cell_id",""))))
      else:
        items_for_dd.append((str(it), str(it)))

    if self._is_blank:
      items_for_dd = [("— select cell —", "")] + items_for_dd

    # Make sure theme roles don’t hide text
    self.drop_down_cell.role = None
    self.drop_down_cell.foreground = "black"
    self.drop_down_cell.background = "white"
    self.drop_down_cell.align = "left"

    self.drop_down_cell.items = items_for_dd
    sel = "" if self._is_blank else (str(d.get("cell_id") or ""))
    self.drop_down_cell.selected_value = sel

    # DEBUG — you should now see this print
    print("RouteCellRow: items:", len(items_for_dd), " sel:", repr(sel))
    print("RouteCellRow.form_show; item keys:", list((self.item or {}).keys()))

    seq = d.get("seq")
    self.text_seq.text = "" if self._is_blank else (str(seq) if seq is not None else "")
    self.button_delete.visible = not self._is_blank

  # Helpers
  def _int_or_none(self, v):
    try:
      return int(v) if (v is not None and str(v).strip() != "") else None
    except:
      return None

  def _create_from_blank(self, seq_val, cell_id):
    if not cell_id:
      return
    if seq_val is None:
      seq_val = self.item.get("seq") or 10
    anvil.server.call("routes_add_cell", self._route_id, {"seq": int(seq_val), "cell_id": cell_id})
    self._parent.on_row_changed()

  def _update_existing(self, patch: dict):
    if not patch:
      return
    anvil.server.call("routes_update_cell", self._route_id, self._index, patch)
    self._parent.on_row_changed()

  # Events
  def text_seq_change(self, **e):
    val = self._int_or_none(self.text_seq.text)
    if val is None:
      Notification("Seq must be an integer").show()
      return
    if self._is_blank:
      self._create_from_blank(val, self.drop_down_cell.selected_value)
    else:
      self._update_existing({"seq": val})

  def drop_down_cell_change(self, **e):
    cell_id = self.drop_down_cell.selected_value
    if self._is_blank:
      seq_val = self._int_or_none(self.text_seq.text) or self.item.get("seq") or 10
      self._create_from_blank(seq_val, cell_id)
    else:
      self._update_existing({"cell_id": cell_id})

  def button_delete_click(self, **e):
    anvil.server.call("routes_remove_cell", self._route_id, self._index)
    self._parent.on_row_changed()


  