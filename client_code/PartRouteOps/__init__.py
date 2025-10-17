from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpsTemplate

class PartRouteOps(PartRouteOpsTemplate):
  """
  Edit per-part overrides for a given route:
    - One row per routing step (seq, cell from the route)
    - Editable: operation_name, cycle_min_per_unit (and extendable fields)
    - Saves per row (upsert); delete clears the override for that seq
  """

  def __init__(self, part_id: str, route_id: str,
               part_name: str = "", route_name: str = "", **kwargs):
    # --- stable state first (so Designer preview won't break) ---
    self._part_id    = part_id
    self._route_id   = route_id
    self._part_name  = part_name or part_id
    self._route_name = route_name or route_id

    self.init_components(**kwargs)

    # Roles / basic wiring
    self.button_back.role = "mydefault-button"

  def form_show(self, **event_args):
    # Header labels
    self.label_part_id.text    = self._part_id
    self.label_part_name.text  = self._part_name
    self.label_route_id.text   = self._route_id
    self.label_route_name.text = self._route_name

    # Preload map for readable cell names & preview
    self.cell_id_to_name = anvil.server.call("get_cell_id_to_name_map") or {}
    try:
      self.label_routing_preview.text = anvil.server.call("routes_preview_string", self._route_id, 12) or ""
    except Exception:
      self.label_routing_preview.text = ""

    # Bubble child events up to here
    self.repeating_panel_ops.set_event_handler("x-row-changed", self._on_row_changed)

    # Load rows
    self._load()

  # ---------- data load ----------
  def _load(self):
    route = anvil.server.call("routes_get", self._route_id) or {}
    routing = sorted(route.get("routing") or [], key=lambda x: x.get("seq", 10))

    # Existing per-part overrides keyed by seq
    existing = anvil.server.call("part_route_ops_list", self._part_id, self._route_id) or []
    existing_by_seq = {op.get("seq"): op for op in existing}

    rows = []
    for step in routing:
      seq = step.get("seq")
      cell_id = step.get("cell_id", "")
      cell_name = self.cell_id_to_name.get(cell_id, cell_id)
      op = existing_by_seq.get(seq, {}) or {}

      rows.append({
        # keep payload flat—row form will read keys directly
        "part_id": self._part_id,
        "route_id": self._route_id,
        "seq": seq,
        "cell_id": cell_id,
        "cell_name": cell_name,
        "operation_name": op.get("operation_name", ""),
        "cycle_min_per_unit": op.get("cycle_min_per_unit", 0.0),
        "consumes": op.get("consumes", []),
        "nc_files": op.get("nc_files", []),
        "work_docs": op.get("work_docs", []),
        "_has_op": bool(op),  # whether there is currently an override doc
      })

    self.repeating_panel_ops.items = rows

  # Child row says it saved or deleted → reload
  def _on_row_changed(self, **event_args):
    # Refresh preview (in case routing changed elsewhere)
    try:
      self.label_routing_preview.text = anvil.server.call("routes_preview_string", self._route_id, 12) or ""
    except Exception:
      pass
    self._load()

  # ---------- nav ----------
  def button_back_click(self, **event_args):
    # If you want to return to PartRecord instead, replace with:
    # open_form("PartRecord", part_id=self._part_id)
    open_form("Nav")

  def button_part_record_click(self, **event_args):
    open_form("PartRecord", part_id=self._part_id)

      


