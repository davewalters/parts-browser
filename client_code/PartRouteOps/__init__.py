from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpsTemplate

class PartRouteOps(PartRouteOpsTemplate):
  def __init__(self, part_id: str, route_id: str,
               part_name: str = "", route_name: str = "", **kwargs):
    self._part_id   = part_id
    self._route_id  = route_id
    self._part_name = part_name or part_id
    self._route_name= route_name or route_id
    self.init_components(**kwargs)

  def form_show(self, **event_args):
    # bind header labels safely here
    self.label_part_id.text   = self._part_id
    self.label_part_name.text = self._part_name
    self.label_route_id.text  = self._route_id
    self.label_route_name.text= self._route_name
    self.button_back.role = "mydefault-button"
    self.cell_id_to_name = anvil.server.call("get_cell_id_to_name_map") or {}
    self.label_routing_preview.text = anvil.server.call("routes_preview_string", self.route_id, 12) or ""

    self.repeating_panel_ops.item_template = PartRouteOps.PartRouteOpRow
    self.set_event_handler("x-row-changed", self._on_row_changed)
    self._load()

  def _load(self):
    route = anvil.server.call("routes_get", self.route_id)
    if not route:
      Notification("Route not found.", style="warning").show()
      self.repeating_panel_ops.items = []
      self.label_routing_preview.text = ""
      return

    # Refresh the preview from server (in case routing changed elsewhere)
    self.label_routing_preview_value.text = anvil.server.call("routes_preview_string", self.route_id, 12) or ""

    routing = sorted(route.get("routing") or [], key=lambda x: x.get("seq", 10))
    existing = anvil.server.call("part_route_ops_list", self.part_id, self.route_id) or []
    existing_by_seq = {op.get("seq"): op for op in existing}

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
          "cell_name": cell_name,
          "operation_name": op.get("operation_name", ""),
          "cycle_min_per_unit": op.get("cycle_min_per_unit", 0.0),
          "consumes": op.get("consumes", []),
          "nc_files": op.get("nc_files", []),
          "work_docs": op.get("work_docs", []),
        }
      })
    self.repeating_panel_ops.items = rows

  # -------- Event handlers --------
  def _on_row_changed(self, **event_args):
    """
    Child rows raise this event after a successful save/delete.
    Keep it simple and reliable: reload to reflect latest server state.
    """
    self._load()

  def button_part_record_click(self, **event_args):
    # Navigate back to where you prefer; example to PartRecord if available:
    try:
      from ..PartRecord import PartRecord
      open_form("PartRecord", part_id=self.part_id)
    except Exception:
      open_form("Nav")

  def button_home_click(self, **event_args):
    open_form("Nav")
      


