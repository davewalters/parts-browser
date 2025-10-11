# client_code/RouteRow/__init__.py
from anvil import *
from ._anvil_designer import RouteRowTemplate
import anvil.server

class RouteRow(RouteRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    # Style the buttons
    if hasattr(self, "button_open_details"):
      self.button_open_details.role = "mydefault-button"
    if hasattr(self, "button_delete"):
      self.button_delete.role = "delete-button"
      # If you’re using icon-only buttons, set:
      # self.button_delete.icon = "trash"

  def form_show(self, **event_args):
    r = dict(self.item or {})
    # Safe-assign helper
    def _set(lbl_name, value):
      c = getattr(self, lbl_name, None)
      if c is not None:
        c.text = value

    _set("label_route_id",       r.get("_id", "") or r.get("route_id", ""))
    _set("label_route_name",     r.get("name", "") or r.get("route_name", "") or "")
    _set("label_product_family", (r.get("product_family") or "") if r.get("product_family") is not None else "")

    # Routing preview (cells-only routing)
    cell_map = r.get("_cell_id_to_name", {}) or {}
    routing  = r.get("routing") or []
    parts = []
    for step in sorted(routing, key=lambda x: x.get("seq", 10)):
      seq = step.get("seq", "")
      cid = step.get("cell_id", "")
      cell_name = cell_map.get(cid, cid)
      parts.append(f"{seq} {cell_name}".strip())
    if len(parts) > 10:
      parts = parts[:10] + ["…"]
    _set("label_routing_preview", " \u2192 ".join(parts))

  def button_open_details_click(self, **event_args):
    prev = ""
    try:
      prev = self.parent.parent.text_filter_name.text or ""
    except Exception:
      pass
    open_form("RouteDetails", route_id=(self.item or {}).get("_id"), prev_filter_name=prev)

  def button_delete_click(self, **event_args):
    r = dict(self.item or {})
    rid = r.get("_id")
    if not rid:
      Notification("No route id to delete.", style="warning").show()
      return
    if not confirm(f"Delete route '{rid}'? This cannot be undone."):
      return
    try:
      anvil.server.call("routes_delete", rid)
      Notification(f"Route {rid} deleted.", style="danger").show()
      # Ask the parent list to reload
      self.parent.raise_event("x-row-deleted")
    except Exception as e:
      alert(f"Delete failed: {e}")






