from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpsTemplate

class PartRouteOps(PartRouteOpsTemplate):
  """
  Stable pattern:
    • Bind header in __init__
    • reload() fetches rows from server (and seeds once if empty)
    • After setting RP items, force-bind visible rows (no timers)
    • No Designer data bindings on row controls
  """

  def __init__(self, part_id: str, route_id: str,
               part_name: str = "", route_name: str = "", **kwargs):
    self._part_id    = part_id
    self._route_id   = route_id
    self._part_name  = part_name or part_id
    self._route_name = route_name or route_id
    self._seed_attempted = False  # guard to seed only once
    super().__init__(**kwargs)

    # Header
    self.label_part_id.text     = self._part_id
    self.label_part_name.text   = self._part_name
    self.label_route_id.text    = self._route_id
    self.label_route_name.text  = self._route_name

    # Buttons
    self.button_home.role = "mydefault-button"
    self.button_part_record.role = "mydefault-button"

    # Preview + cell map
    try:
      self.label_route_preview.text = anvil.server.call(
        "routes_preview_string", self._route_id, 12
      ) or ""
    except Exception:
      self.label_route_preview.text = ""

    self._cell_id_to_name = anvil.server.call("get_cell_id_to_name_map") or {}
    # [(display, value)]
    self._cell_items = [(name, cid) for cid, name in self._cell_id_to_name.items()]

    # Child rows will call back here
    self.set_event_handler("x-row-changed", self._on_row_changed)

    # Initial load
    self.reload()

  # ---------- data load ----------
  def reload(self):
    try:
      rows = anvil.server.call("part_route_ops_list", self._part_id, self._route_id) or []
      if not rows and not self._seed_attempted:
        # Seed once from route template, then reload
        self._seed_attempted = True
        anvil.server.call("part_route_ops_seed_from_route", self._part_id, self._route_id)
        rows = anvil.server.call("part_route_ops_list", self._part_id, self._route_id) or []

      # Enrich with cell_name + dropdown items
      for r in rows:
        cid = r.get("cell_id") or ""
        r["cell_name"]   = self._cell_id_to_name.get(cid, cid)
        r["_cell_items"] = list(self._cell_items)  # give each row its own copy

      self.repeating_panel_ops.items = rows
      self._force_bind_rows()

    except Exception as e:
      self.repeating_panel_ops.items = []
      Notification(f"Load failed: {e}", style="danger").show()

  def _force_bind_rows(self):
    # Nudge visible rows to bind now (works with DataRowPanel item templates)
    try:
      for row in getattr(self.repeating_panel_ops, "get_components", lambda: [])():
        if hasattr(row, "_bind_from_item"):
          row._bind_from_item()
    except Exception:
      pass

  # ---------- child-row callback ----------
  def _on_row_changed(self, **event_args):
    self.reload()

  # ---------- navigation ----------
  def button_home_click(self, **event_args):
    open_form("Nav")

  def button_part_record_click(self, **event_args):
    open_form("PartRecord", part_id=self._part_id)


      


