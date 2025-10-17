# client_code/PartRouteOps/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpsTemplate

class PartRouteOps(PartRouteOpsTemplate):
  """
  PartRouteOps — stable pattern:
    • Bind header and load rows in __init__ (not form_show)
    • Provide reload() that rows call after any change
    • No timers, no row caching
  """

  def __init__(self, part_id: str, route_id: str,
               part_name: str = "", route_name: str = "", **kwargs):
    self._part_id    = part_id
    self._route_id   = route_id
    self._part_name  = part_name or part_id
    self._route_name = route_name or route_id
    self._cell_items = []   # [(cell_name, cell_id)]
    self.init_components(**kwargs)

    # Roles (optional)
    self.button_home.role = "mydefault-button"
    self.button_part_record.role = "mydefault-button"

    # Bind header NOW (no form_show)
    self.label_part_id.text     = self._part_id
    self.label_part_name.text   = self._part_name
    self.label_route_id.text    = self._route_id
    self.label_route_name.text  = self._route_name

    # Preload preview + rows
    try:
      self.label_route_preview.text = anvil.server.call(
        "routes_preview_string", self._route_id, 12
      ) or ""
    except Exception:
      self.label_route_preview.text = ""

    self.reload()  # initial load

  # Public reload the rows from server (rows call this via parent)
  def reload(self):
    """Server is source of truth; re-query and bind rows."""
    try:
      cell_map = anvil.server.call("get_cell_id_to_name_map") or {}
      self._cell_items = [(nm, cid) for cid, nm in cell_map.items()]

      rows = anvil.server.call("part_route_ops_list", self._part_id, self._route_id) or []
      rows = sorted(rows, key=lambda r: int(r.get("seq", 0)))
      for r in rows:
        r["_cell_items"] = list(self._cell_items)
        r["cell_name"] = cell_map.get(r.get("cell_id",""), r.get("cell_id",""))
      self.repeating_panel_ops.items = rows
    except Exception as e:
      self.repeating_panel_ops.items = []
      Notification(f"Load failed: {e}", style="danger").show()

  # Navigation
  def button_home_click(self, **event_args):
    open_form("Nav")

  def button_part_record_click(self, **event_args):
    open_form("PartRecord", part_id=self._part_id)

      


