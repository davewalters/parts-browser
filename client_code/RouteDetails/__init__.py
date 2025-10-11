from anvil import *
import anvil.server
from ._anvil_designer import RouteDetailsTemplate

class RouteDetails(RouteDetailsTemplate):
  def __init__(self, route_id=None, **kwargs):
    self.init_components(**kwargs)
    self.button_resequence.role = "new-button"
    self.button_back.role = "mydefault-button"
    self.repeating_panel_cells.role = "scrolling-panel"

    # ✅ Make sure the RepeatingPanel uses the right template
    self.repeating_panel_cells.item_template = "RouteDetails.RouteCellRow"

    self.route_id = route_id or None
    self._cells = []
    self._cell_items = []
    self._ensure_route_exists()
    self._load()

  def _ensure_route_exists(self):
    if self.route_id and anvil.server.call("routes_get", self.route_id):
      return
    rid = anvil.server.call("routes_next_id")
    doc = anvil.server.call(
      "routes_create",
      {"_id": rid, "name": "", "product_family": "", "routing": []}  # product_family as empty string (model requires str)
    )
    self.route_id = doc["_id"]

  def _load(self):
    route = anvil.server.call("routes_get", self.route_id) or {}
    self.doc = route

    # Header
    self.label_route_id.text = route.get("_id", "") or route.get("route_id", "")
    self.text_route_name.text = route.get("name", "") or route.get("route_name", "") or ""
    self.text_product_family.text = route.get("product_family", "") or ""

    # Cells for dropdowns
    self._cells = anvil.server.call("cells_list_route_ui") or []
    # Normalize to list[(name, cell_id)]
    self._cell_items = [(str(c.get("name","")), str(c.get("cell_id",""))) for c in self._cells if c.get("cell_id")]
    print("cells_list_route_ui returned:", len(self._cell_items))  # DEBUG

    # Build items for RP
    routing = (route.get("routing") or [])[:]
    routing.sort(key=lambda r: ((r.get("seq") if isinstance(r.get("seq"), (int, float)) else 1e9),
                                r.get("cell_id", "")))
    name_by_id = {str(c.get("cell_id")): str(c.get("name","")) for c in self._cells}

    items = []
    for step in routing:
      items.append({
        "seq": step.get("seq"),
        "cell_id": str(step.get("cell_id","")),
        "cell_name": name_by_id.get(str(step.get("cell_id","")), ""),
        "_is_blank": False,
        "_cell_items": list(self._cell_items),   # 👈 inject choices per row
      })
    # Sentinel
    items.append({
      "seq": self._suggest_next_seq(items),
      "cell_id": "",
      "cell_name": "",
      "_is_blank": True,
      "_cell_items": list(self._cell_items),
    })

    self.repeating_panel_cells.items = items
    self.label_count.text = f"{max(0, len(items)-1)} steps"

  def _suggest_next_seq(self, items) -> int:
    seqs = [i.get("seq") for i in items if not i.get("_is_blank")]
    seqs = [int(s) for s in seqs if isinstance(s, (int, float)) or (isinstance(s, str) and s.isdigit())]
    return (max(seqs) + 10) if seqs else 10

  # Header change
  def text_route_name_change(self, **e):
    name = (self.text_route_name.text or "").strip()
    try:
      anvil.server.call("routes_update", self.route_id, {"name": name})
    except Exception as ex:
      alert(f"Rename failed: {ex}")

  def text_product_family_change(self, **e):
    fam = (self.text_product_family.text or "").strip()
    try:
      anvil.server.call("routes_update", self.route_id, {"product_family": fam})
    except Exception as ex:
      alert(f"Update failed: {ex}")

  # Row callbacks
  def get_cell_dropdown_items(self):
    return list(self._cell_items)

  def on_row_changed(self):
    self._load()

  def button_resequence_click(self, **e):
    try:
      updated = anvil.server.call("routes_resequence", self.route_id)
      if not updated:
        alert("Route not found."); return
      self._load()
      Notification("Route resequenced to 10,20,30…").show()
    except Exception as ex:
      alert(f"Resequence failed: {ex}")

  def button_back_click(self, **e):
    open_form("Nav")




