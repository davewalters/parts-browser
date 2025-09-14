from ._anvil_designer import RouteDetailsTemplate
from anvil import *
import anvil.server

class RouteDetails(RouteDetailsTemplate):
  def __init__(self, route_id: str | None, **kwargs):
    self.init_components(**kwargs)
    self.route_id = route_id or None
    self._cells = []
    self._cell_items = []
    self.repeating_panel_ops.item_template = RouteOpRow
    self._ensure_route()
    self._load()

  # ---------- create-if-needed ----------
  def _ensure_route(self):
    """
    If route_id is None or not found, prompt the user to create a new route.
    Allocates route_id immediately (DB create).
    """
    if self.route_id:
      # check it exists
      r = anvil.server.call("routes_get", self.route_id)
      if r:
        return

    # Prompt to create
    name_tb = TextBox(placeholder="Route name (required)")
    fam_tb  = TextBox(placeholder="Product family (optional)")
    res = alert(ColumnPanel(items=[("Name", name_tb), ("Product family", fam_tb)]),
                title="Create Route", buttons=["Create","Cancel"])
    if res != "Create":
      # navigate away if you prefer; for now keep form inert
      return
    name = (name_tb.text or "").strip()
    if not name:
      Notification("Route name is required").show()
      return self._ensure_route()

    try:
      doc = anvil.server.call("routes_create", name=name, product_family=(fam_tb.text or "").strip() or None)
    except Exception as ex:
      alert(f"Failed to create route: {ex}")
      return self._ensure_route()
    self.route_id = doc["_id"]

  # ---------- data load/bind ----------
  def _load(self):
    route = anvil.server.call("routes_get", self.route_id) or {}
    self.doc = route

    # Header bind (route id/name/family)
    self.label_route_id.text = route.get("_id","") or route.get("route_id","")
    self.text_route_name.text = route.get("name","") or route.get("route_name","")
    self.text_product_family.text = route.get("product_family","") or ""

    # Cells for dropdowns
    self._cells = anvil.server.call("cells_list") or []
    self._cell_items = [(c.get("name",""), c.get("cell_id")) for c in self._cells if c.get("cell_id")]

    # Routing rows
    routing = (route.get("routing") or [])[:]
    routing.sort(key=lambda r: ((r.get("seq") if isinstance(r.get("seq"), (int,float)) else 1e9), r.get("cell_id","")))
    name_by_id = {c.get("cell_id"): c.get("name","") for c in self._cells}

    items = []
    for step in routing:
      items.append({
        "seq": step.get("seq"),
        "cell_id": step.get("cell_id",""),
        "cell_name": name_by_id.get(step.get("cell_id"), step.get("cell_id","")),
        "_is_blank": False
      })
    # Sentinel blank row for quick add (default next seq)
    items.append({"seq": self._suggest_next_seq(items), "cell_id": "", "cell_name": "", "_is_blank": True})

    self.repeating_panel_ops.items = items
    self.label_count.text = f"{max(0, len(items)-1)} steps"

  def _suggest_next_seq(self, items) -> int:
    seqs = [i.get("seq") for i in items if not i.get("_is_blank")]
    seqs = [int(s) for s in seqs if isinstance(s, (int,float)) or (isinstance(s,str) and s.isdigit())]
    return (max(seqs) + 10) if seqs else 10

  # ---------- header update-on-change ----------
  def text_route_name_change(self, **e):
    name = (self.text_route_name.text or "").strip()
    try:
      anvil.server.call("routes_update", self.route_id, {"name": name or None})
    except Exception as ex:
      alert(f"Rename failed: {ex}")
    # no reload necessary

  def text_product_family_change(self, **e):
    fam = (self.text_product_family.text or "").strip()
    try:
      anvil.server.call("routes_update", self.route_id, {"product_family": fam or None})
    except Exception as ex:
      alert(f"Update failed: {ex}")

  # ---------- child rows can call back ----------
  def get_cell_dropdown_items(self):
    return list(self._cell_items)

  def on_row_changed(self):
    self._load()

  # ---------- resequence ----------
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


