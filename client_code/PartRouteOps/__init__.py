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

    # header
    self.label_part_id.text     = self._part_id
    self.label_part_name.text   = self._part_name
    self.label_route_id.text    = self._route_id
    self.label_route_name.text  = self._route_name
    self.button_home.role = "mydefault-button"
    self.button_part_record.role = "mydefault-button"

    try:
      self.label_route_preview.text = anvil.server.call(
        "routes_preview_string", self._route_id, 12
      ) or ""
    except Exception:
      self.label_route_preview.text = ""

    self.cell_id_to_name = anvil.server.call("get_cell_id_to_name_map") or {}
    self._load()
  
  def reload(self):
    self._load()
    
  def _load(self):
    print("[PRO] _load for", self._part_id, self._route_id)
    rows = anvil.server.call("part_route_ops_list", self._part_id, self._route_id) or []
    print("[PRO] rows returned:", len(rows))

    cell_items = [(name, cid) for cid, name in self.cell_id_to_name.items()]
    fat_rows = []
    for r in rows:
      cid = r.get("cell_id") or ""
      r["cell_name"]   = self.cell_id_to_name.get(cid, cid)
      r["_cell_items"] = [("— select cell —", "")] + cell_items
      r["part_id"]     = self._part_id
      r["route_id"]    = self._route_id
      fat_rows.append(r)

    self.repeating_panel_ops.items = []    # <- clear first
    self.repeating_panel_ops.items = fat_rows
    print("[PRO] items bound:", len(fat_rows))
    print("[PRO] items: ", fat_rows)

  # event from row to reload after insert/delete
  def _on_row_changed(self, **e):
    self._load()

  # navigation
  def button_home_click(self, **event_args):
    open_form("Nav")

  def button_part_record_click(self, **event_args):
    open_form("PartRecord", part_id=self._part_id)

      


