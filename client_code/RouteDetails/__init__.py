from anvil import *
import anvil.server
from ._anvil_designer import RouteDetailsTemplate

class RouteDetails(RouteDetailsTemplate):
  """
  Edit a Route (name, product family, and ordered cell steps).
  - Creates a new route immediately if route_id is None/invalid (so header edits can save).
  - Header fields auto-save on blur/Enter and won’t be clobbered while you’re typing.
  - Steps live in a repeating panel; the last row is a sentinel “blank” row.
    As soon as seq + cell are both provided on the sentinel row (in any order), a
    real step is created; parent reloads; a new sentinel is appended.
  """

  def __init__(self, route_id=None, prev_filter_name="", **kwargs):
    self.init_components(**kwargs)
    
    self.text_route_name.set_event_handler("change",        self.text_route_name_change)
    self.text_route_name.set_event_handler("lost_focus",    self.text_route_name_lost_focus)
    self.text_route_name.set_event_handler("pressed_enter", self.text_route_name_pressed_enter)
    
    self.text_product_family.set_event_handler("change",        self.text_product_family_change)
    self.text_product_family.set_event_handler("lost_focus",    self.text_product_family_lost_focus)
    self.text_product_family.set_event_handler("pressed_enter", self.text_product_family_pressed_enter)

    # Roles (optional)
    self.button_resequence.role = "new-button"
    self.button_back.role       = "mydefault-button"
    self.repeating_panel_cells.role = "scrolling-panel"

    # State
    self.route_id = route_id or None
    self.prev_filter_name = prev_filter_name or ""
    self._cells = []              # [{cell_id, name}, ...]
    self._cell_items = []         # [(name, cell_id), ...]
    self._header_dirty = False    # guard to avoid clobbering UI while typing

    # Child rows bubble this back up after add/update/delete
    self.repeating_panel_cells.set_event_handler("x-row-changed", self._on_row_changed)

    # Ensure there is a route doc to edit, then load/bind
    self._ensure_route_exists()
    self._load()

  # ---------- bootstrap ----------
  def _ensure_route_exists(self):
    """Ensure a blank route exists so subsequent 'update on change' can persist."""
    if self.route_id:
      if anvil.server.call("routes_get", self.route_id):
        return
    rid = anvil.server.call("routes_next_id")
    # Use empty strings (not None) to satisfy model validators
    doc = anvil.server.call("routes_create", {
      "_id": rid, "name": "", "product_family": "", "routing": []
    })
    self.route_id = doc["_id"]

  # ---------- load/bind ----------
  def _bind_header_from_doc(self, route):
    """Bind header fields; avoid overwriting while user is typing."""
    self.label_route_id.text = route.get("_id", "") or route.get("route_id", "")
    if not self._header_dirty:
      self.text_route_name.text     = route.get("name", "") or route.get("route_name", "") or ""
      self.text_product_family.text = route.get("product_family", "") or ""

  def _load(self):
    route = anvil.server.call("routes_get", self.route_id) or {}
    self.doc = route

    # Header
    self._bind_header_from_doc(route)

    # Dropdown choices for rows
    self._cells = anvil.server.call("cells_list_route_ui") or []
    self._cell_items = [(c.get("name", ""), c.get("cell_id")) for c in self._cells if c.get("cell_id")]

    # Build routing rows
    routing = (route.get("routing") or [])[:]
    routing.sort(key=lambda r: (
      (r.get("seq") if isinstance(r.get("seq"), (int, float)) else 1e9),
      r.get("cell_id", "")
    ))
    name_by_id = {c.get("cell_id"): c.get("name", "") for c in self._cells}

    items = []
    for step in routing:
      items.append({
        "seq": step.get("seq"),
        "cell_id": step.get("cell_id", ""),
        "cell_name": name_by_id.get(step.get("cell_id"), step.get("cell_id", "")),
        "_is_blank": False,
        "_cell_items": list(self._cell_items),   # pass choices to row
        "_route_id": self.route_id,              # pass route id to row
      })

    # Sentinel row (always last)
    items.append({
      "seq": self._suggest_next_seq(items),
      "cell_id": "",
      "cell_name": "",
      "_is_blank": True,
      "_cell_items": [("— select cell —", ""), *self._cell_items],
      "_route_id": self.route_id,
    })

    self.repeating_panel_cells.items = items
    self._rebind_visible_rows()  # makes dropdowns populate immediately
    self.label_count.text = f"{max(0, len(items)-1)} steps"

  def _suggest_next_seq(self, items) -> int:
    seqs = [i.get("seq") for i in items if not i.get("_is_blank")]
    seqs = [int(s) for s in seqs if isinstance(s, (int, float)) or (isinstance(s, str) and str(s).isdigit())]
    return (max(seqs) + 10) if seqs else 10

  def _rebind_visible_rows(self):
    """Force row templates to refresh now (helps right after items= assignment)."""
    try:
      for row_form in getattr(self.repeating_panel_cells, 'get_components', lambda: [])():
        if hasattr(row_form, 'refreshing_data_bindings'):
          row_form.refreshing_data_bindings()
    except Exception:
      pass

  # ---------- header autosave ----------
  def _save_header_if_dirty(self):
    if not self._header_dirty:
      return
    name = (self.text_route_name.text or "").strip()
    fam  = (self.text_product_family.text or "").strip()
    try:
      anvil.server.call("routes_update", self.route_id, {"name": name, "product_family": fam})
      self._header_dirty = False
    except Exception as ex:
      Notification(f"Header save failed: {ex}", style="warning").show()

  # Wire these in the Designer to the two TextBoxes:
  def text_route_name_change(self, **e):
    self._header_dirty = True
  def text_route_name_lost_focus(self, **e):
    self._save_header_if_dirty()
  def text_route_name_pressed_enter(self, **e):
    self._save_header_if_dirty()

  def text_product_family_change(self, **e):
    self._header_dirty = True
  def text_product_family_lost_focus(self, **e):
    self._save_header_if_dirty()
  def text_product_family_pressed_enter(self, **e):
    self._save_header_if_dirty()

  # ---------- row -> parent callback ----------
  def _on_row_changed(self, **e):
    # Row notifies us to reload after add/update/delete
    self._save_header_if_dirty()
    self._load()

  # ---------- actions ----------
  def button_resequence_click(self, **e):
    try:
      updated = anvil.server.call("routes_resequence", self.route_id)
      if not updated:
        alert("Route not found.")
        return
      self._load()
      Notification("Route resequenced to 10,20,30…").show()
    except Exception as ex:
      alert(f"Resequence failed: {ex}")

  def button_back_click(self, **e):
    open_form("Routes", filter_name=self.prev_filter_name)






