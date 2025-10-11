# client_code/RouteRow/__init__.py
from anvil import *
from ._anvil_designer import RouteRowTemplate

class RouteRow(RouteRowTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.button_open_details.role = "mydefault-button"
    # EXPLICITLY hook the refresh event so DataRowPanel will call it
    self.set_event_handler("refreshing_data_bindings", self._refresh)

  def _refresh(self, **event_args):
    r = dict(self.item or {})

    # Helper to assign text only if the label exists
    def _set(lbl_name, value):
      c = getattr(self, lbl_name, None)
      if c is not None:
        c.text = value

    _set("label_route_id",       r.get("_id", "") or r.get("route_id", ""))
    _set("label_route_name",     r.get("name", "") or r.get("route_name", ""))
    _set("label_product_family", r.get("product_family", "") or "")

    # Build preview from 'routing' (list of {'seq','cell_id'})
    cell_map = r.get("_cell_id_to_name", {}) or {}
    routing  = r.get("routing") or []
    parts = []
    for step in sorted(routing, key=lambda x: x.get("seq", 10)):
      seq = step.get("seq", "")
      cid = step.get("cell_id", "")
      parts.append(f"{seq} {cell_map.get(cid, cid)}".strip())

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



