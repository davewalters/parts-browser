from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpsTemplate

class PartRouteOps(PartRouteOpsTemplate):
  def __init__(self, part_id: str, route_id: str,
               part_name: str = "", route_name: str = "", **kwargs):
    # Store args early so we can log them even if init blows up
    self._part_id    = part_id
    self._route_id   = route_id
    self._part_name  = part_name or part_id
    self._route_name = route_name or route_id

    print("[PRO] __init__ start",
          "part_id=", self._part_id,
          "route_id=", self._route_id,
          "part_name=", self._part_name,
          "route_name=", self._route_name)

    self.init_components(**kwargs)

    # Optional roles
    self.button_home.role = "mydefault-button"
    self.button_part_record.role = "mydefault-button"
    
    # Bind header IMMEDIATELY (no form_show dependency)
    try:
      self.label_part_id.text    = self._part_id
      self.label_part_name.text  = self._part_name
      self.label_route_id.text   = self._route_id
      self.label_route_name.text = self._route_name
      print("[PRO] Header bound")
    except Exception as e:
      print("[PRO][ERR] binding header:", e)

    # Parent listens for row-save callback
    self.repeating_panel_ops.set_event_handler("x-row-changed", self.on_row_changed)

    # Preload the cell map (with logging)
    self._cell_id_to_name = {}
    try:
      self._cell_id_to_name = anvil.server.call("get_cell_id_to_name_map") or {}
      print("[PRO] cell_id_to_name loaded:", len(self._cell_id_to_name))
    except Exception as e:
      print("[PRO][ERR] get_cell_id_to_name_map:", e)

    # Route preview (support either label name)
    try:
      preview = anvil.server.call("routes_preview_string", self._route_id, 12) or ""
      self.label_route_preview.text = preview
      print("[PRO] preview ok:", preview)
    except Exception as e:
      print("[PRO][ERR] routes_preview_string:", e)

    # Initial load
    self._load()
    print("[PRO] __init__ done")

  # -----------------------------
  # Load/refresh
  # -----------------------------
  def _load(self):
    print("[PRO] _load start for route:", self._route_id)
    route = None
    try:
      route = anvil.server.call("routes_get", self._route_id)
      print("[PRO] routes_get ok. route keys:", list((route or {}).keys()))
    except Exception as e:
      print("[PRO][ERR] routes_get:", e)
      route = None

    if not route:
      Notification("Route not found.", style="warning").show()
      self.repeating_panel_ops.items = []
      self.label_route_preview.text = ""
      return

    # Keep preview fresh (and log)
    try:
      preview = anvil.server.call("routes_preview_string", self._route_id, 12) or ""
      self.label_route_preview.text = preview
      print("[PRO] preview refreshed:", preview)
    except Exception as e:
      print("[PRO][ERR] refresh preview:", e)

    # Routing + existing ops
    try:
      routing = sorted(route.get("routing") or [], key=lambda x: x.get("seq", 10))
      print("[PRO] routing len:", len(routing), routing)
    except Exception as e:
      print("[PRO][ERR] reading routing:", e)
      routing = []

    existing = []
    try:
      existing = anvil.server.call("part_route_ops_list", self._part_id, self._route_id) or []
      print("[PRO] part_route_ops_list len:", len(existing))
    except Exception as e:
      print("[PRO][ERR] part_route_ops_list:", e)

    existing_by_seq = {op.get("seq"): op for op in existing}

    rows = []
    for step in routing:
      seq     = step.get("seq")
      cell_id = step.get("cell_id", "")
      cell_nm = self._cell_id_to_name.get(cell_id, cell_id)
      op      = existing_by_seq.get(seq, {}) or {}

      rows.append({
        "part_id": self._part_id,
        "route_id": self._route_id,
        "seq": seq,
        "cell_id": cell_id,
        "cell_name": cell_nm,
        "operation_name": op.get("operation_name", ""),
        "cycle_min_per_unit": float(op.get("cycle_min_per_unit", 0.0) or 0.0),
        "consumes": op.get("consumes", []),
        "nc_files": op.get("nc_files", []),
        "work_docs": op.get("work_docs", []),
      })

    print("[PRO] rows to bind:", len(rows))
    self.repeating_panel_ops.items = rows

  # Row signals a save happened
  def on_row_changed(self, **event_args):
    print("[PRO] on_row_changed -> reload")
    self._load()

  # ---------- nav ----------
  def button_home_click(self, **event_args):
    open_form("Nav")

  def button_part_record_click(self, **event_args):
    open_form("PartRecord", part_id=self._part_id)

      


