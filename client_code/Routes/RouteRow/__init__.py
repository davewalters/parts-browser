# client_code/RouteRow/__init__.py
from anvil import *
from ._anvil_designer import RouteRowTemplate

class RouteRow(RouteRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_open_details.role = "mydefault-button"

  def form_show(self, **event_args):
    r = self.item or {}
    #self.label_route_id.text = r.get("_id", "")
    self.label_route_name.text = r.get("name", "")
    self.label_product_family.text = r.get("product_family", "")

    # Compose readable preview from operations: [{seq, cell_id}]
    cell_map = r.get("_cell_id_to_name", {}) or {}
    ops = (r.get("operations") or [])
    parts = []
    for op in sorted(ops, key=lambda x: x.get("seq", 10)):
      seq = op.get("seq", "")
      cell_name = cell_map.get(op.get("cell_id", ""), op.get("cell_id", ""))
      parts.append(f"{seq} {cell_name}".strip())
    # shorten if long
    if len(parts) > 10:
      parts = parts[:10] + ["…"]
    self.label_routing_preview.text = " \u2192 ".join(parts)

  def button_open_details_click(self, **event_args):
    #from ..RouteDetails import RouteDetails
    parent = self.parent
    prev = ""
    try:
      prev = parent.parent.text_filter_name.text or ""
    except Exception:
      pass
    open_form("RouteDetails", route_id=self.item.get("_id"), prev_filter_name=prev)


