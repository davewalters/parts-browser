from anvil import *
from ._anvil_designer import RouteRowTemplate

class RouteRow(RouteRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_open_details.role = "mydefault-button"

  # IMPORTANT: DataRowPanel rows should bind in refreshing_data_bindings
  def refreshing_data_bindings(self, **event_args):
    r = dict(self.item or {})

    # Basic fields
    #self.label_route_id.text      = r.get("_id", "") or r.get("route_id", "")
    self.label_route_name.text    = r.get("name", "") or r.get("route_name", "")
    self.label_product_family.text= r.get("product_family", "") or ""

    # Preview from routing (list of {'seq','cell_id'})
    cell_map = r.get("_cell_id_to_name", {}) or {}
    routing = r.get("routing") or []
    parts = []
    for step in sorted(routing, key=lambda x: x.get("seq", 10)):
      seq = step.get("seq", "")
      cid = step.get("cell_id", "")
      cell_name = cell_map.get(cid, cid)
      parts.append(f"{seq} {cell_name}".strip())

    if len(parts) > 10:
      parts = parts[:10] + ["…"]

    self.label_routing_preview.text = " \u2192 ".join(parts)

  def button_open_details_click(self, **event_args):
    # Pick up the current filter for a nicer back-nav
    prev = ""
    try:
      prev = self.parent.parent.text_filter_name.text or ""
    except Exception:
      pass
    open_form("RouteDetails", route_id=(self.item or {}).get("_id"), prev_filter_name=prev)



