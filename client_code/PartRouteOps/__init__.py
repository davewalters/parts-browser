# client_code/PartRouteOps/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import PartRouteOpsTemplate

class PartRouteOps(PartRouteOpsTemplate):
  """
  Per-part operations (authoritative for a part+route).
  - Header + rows bind in __init__ (no form_show).
  - If there are no part ops rows yet, seed them from the route template (silent).
  - Rows can edit seq/cell and insert/delete; parent reloads on 'x-row-changed'.
  """

  def __init__(self, part_id: str, route_id: str,
               part_name: str = "", route_name: str = "", **kwargs):
    self._part_id    = part_id
    self._route_id   = route_id
    self._part_name  = part_name or part_id
    self._route_name = route_name or route_id

    self._cell_items = []  # [(display_name, cell_id), ...]

    self.init_components(**kwargs)

    # --- Header (bind here, not in form_show) ---
    self.label_part_id.text            = self._part_id
    self.label_part_name.text          = self._part_name
    self.label_route_id.text           = self._route_id
    self.label_route_name.text         = self._route_name
    self.button_home.role              = "mydefault-button"
    self.button_part_record.role       = "mydefault-button"
    
    # Parent listens for row changes -> reload
    self.repeating_panel_ops.set_event_handler("x-row-changed", self._on_row_changed)

    # Preload cell dropdown choices
    try:
      cells = anvil.server.call("cells_list_route_ui") or []
    except Exception:
      cells = []
    self._cell_items = [(c.get("name",""), c.get("cell_id")) for c in cells if c.get("cell_id")]

    # Route preview (template only)
    try:
      preview = anvil.server.call("routes_preview_string", self._route_id, 12) or ""
    except Exception:
      preview = ""
    self.label_route_preview.text = preview

    # Initial load of rows
    self._load()

  # -----------------------------
  # Load & bind rows
  # -----------------------------
  def _load(self):
    # 1) Fetch rows (seed silently if empty)
    try:
      rows = anvil.server.call("part_route_ops_list", self._part_id, self._route_id) or []
      if not rows:
        # seed from route template, then load again
        anvil.server.call("part_route_ops_seed", self._part_id, self._route_id)
        rows = anvil.server.call("part_route_ops_list", self._part_id, self._route_id) or []
    except Exception as e:
      rows = []
      Notification(f"Load failed: {e}", style="danger").show()

    # 2) Transform for RP (inject dropdown choices)
    items = []
    for op in rows:
      items.append({
        "part_id": self._part_id,
        "route_id": self._route_id,
        "seq": op.get("seq"),
        "cell_id": op.get("cell_id") or "",
        "operation_name": op.get("operation_name", ""),
        "cycle_min_per_unit": op.get("cycle_min_per_unit", 0.0),
        "consumes": op.get("consumes", []),
        "nc_files": op.get("nc_files", []),
        "work_docs": op.get("work_docs", []),
        "_cell_items": list(self._cell_items),
      })

    # 3) Bind to RP and force visible rows to refresh immediately
    self.repeating_panel_ops.items = items
    try:
      for row_form in getattr(self.repeating_panel_ops, "get_components", lambda: [])():
        if hasattr(row_form, "refreshing_data_bindings"):
          row_form.refreshing_data_bindings()
    except Exception:
      pass

  # -----------------------------
  # Row callback (insert/update/delete)
  # -----------------------------
  def _on_row_changed(self, **event_args):
    self._load()

  # -----------------------------
  # Navigation
  # -----------------------------
  def button_home_click(self, **event_args):
    open_form("Nav")

  def button_part_record_click(self, **event_args):
    open_form("PartRecord", part_id=self._part_id)

      


