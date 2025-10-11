from ._anvil_designer import RouteCellRowTemplate
from anvil import *
import anvil.server

class RouteCellRow(RouteCellRowTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)
    # Defer parent lookups until form_show()
    self._parent = None           # RouteDetails (set in form_show)
    self._route_id = None
    self._index = None
    self._is_blank = False

  def form_show(self, **e):
    # Wire parent & route_id now that the row is attached
    rp = self.parent                       # RepeatingPanel
    self._parent = rp.parent               # RouteDetails
    self._route_id = getattr(self._parent, "route_id", None)

    items = list(rp.items or [])
    self._index = items.index(self.item)
    self._is_blank = bool(self.item.get("_is_blank"))

    # Seq field
    seq = self.item.get("seq")
    self.text_seq.text = "" if self._is_blank else (str(seq) if seq is not None else "")

    # Cell dropdown
    cell_items = self._parent.get_cell_dropdown_items()  # [(name, cell_id), ...]
    if self._is_blank:
      cell_items = [("— select cell —", None)] + cell_items
    self.drop_down_cell.items = cell_items
    self.drop_down_cell.selected_value = None if self._is_blank else self.item.get("cell_id", "")

    # Only real rows can be deleted
    self.button_delete.visible = not self._is_blank


  # ---------- helpers ----------
  def _int_or_none(self, v):
    try:
      return int(v) if (v is not None and str(v).strip() != "") else None
    except:
      return None

  def _create_from_blank(self, seq_val, cell_id):
    if not cell_id:
      return  # need a cell to create
    if seq_val is None:
      seq_val = self.item.get("seq") or 10
    anvil.server.call("routes_add_cell", self._route_id, {"seq": int(seq_val), "cell_id": cell_id})
    self._parent.on_row_changed()

  def _update_existing(self, patch: dict):
    if not patch:
      return
    anvil.server.call("routes_update_cell", self._route_id, self._index, patch)
    self._parent.on_row_changed()

  # ---------- update-on-change ----------
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
  