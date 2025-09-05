# client_code/PartRouteOps/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpsTemplate
from ..PartRouteOpRow import PartRouteOpRow

class PartRouteOps(PartRouteOpsTemplate):
  """
  Edit per-part operation content for a given (part_id, route_id).
  """
  def __init__(self, part_id: str, route_id: str, part_name: str = "", route_name: str = "", **kwargs):
    self.init_components(**kwargs)

    self.button_back.role = "mydefault-button"
    self.button_refresh.role = "mydefault-button"

    self.part_id = part_id
    self.route_id = route_id
    self.part_name = part_name or ""
    self.route_name = route_name or ""

    # Cell name map for display
    self.cell_id_to_name = anvil.server.call("get_cell_id_to_name_map") or {}

    # Header labels
    self.label_part_id_value.text = part_id
    self.label_part_name_value.text = self.part_name
    self.label_route_id_value.text = route_id
    self.label_route_name_value.text = self.route_name

    # Template for rows
    self.repeating_panel_ops.item_template = PartRouteOpRow

    # Load route steps + existing per-part ops
    self._load()

  def _load(self):
    route = anvil.server.call("routes_get", self.route_id)
    if not route:
      Notification("Route not found.", style="warning").show()
      return

    routing = sorted(route.get("routing") or [], key=lambda x: x.get("seq", 10))
    existing = anvil.server.call("part_route_ops_list", self.part_id, self.route_id) or []
    existing_by_seq = {op.get("seq"): op for op in existing}

    # Build rows: one per routing step (seq/cell), hydrated with per-part op content if exists
    rows = []
    for step in routing:
      seq = step.get("seq")
      cell_id = step.get("cell_id", "")
      cell_name = self.cell_id_to_name.get(cell_id, cell_id)

      op = existing_by_seq.get(seq, {})
      rows.append({
        "_row": {
          "part_id": self.part_id,
          "route_id": self.route_id,
          "seq": seq,
          "cell_name": cell_name,  # display only
          # per-part fields:
          "operation_name": op.get("operation_name", ""),
          "cycle_min_per_unit": op.get("cycle_min_per_unit", 0.0),
          "consumes": op.get("consumes", []),
          "nc_files": op.get("nc_files", []),
          "work_docs": op.get("work_docs", []),
        }
      })

    self.repeating_panel_ops.items = rows

  def button_refresh_click(self, **event_args):
    self._load()

  def button_back_click(self, **event_args):
    # Go back to the part or route screen in your app; placeholder:
    try:
      from ..PartRecord import PartRecord
      open_form("PartRecord", part_id=self.part_id)
    except Exception:
      open_form("Home")

