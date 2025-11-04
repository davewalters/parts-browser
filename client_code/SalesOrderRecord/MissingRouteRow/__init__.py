from anvil import *
import anvil.server
from ._anvil_designer import MissingRouteRowTemplate

class MissingRouteRow(MissingRouteRowTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)
    # Kill designer data bindings
    for w in [getattr(self, "label_part_id", None),
              getattr(self, "label_reason", None),
              getattr(self, "button_open_part", None),
              getattr(self, "button_open_ops", None)]:
      if w and hasattr(w, "data_bindings"):
        try:
          w.data_bindings = []
        except Exception:
          pass
    self.set_item(self.item or kwargs.get("item") or {})

  def set_item(self, item):
    i = dict(item or {})
    if hasattr(self, "label_part_id"):
      self.label_part_id.text = i.get("part_id") or ""
    if hasattr(self, "label_reason"):
      self.label_reason.text = i.get("reason") or "no route"

  # ---- helpers ----
  def _find_sales_order_context(self):
    """
    Walk up to locate the SalesOrderRecord instance to get order_id.
    If not found, try get_open_form().content.
    """
    p = self.parent
    while p:
      if hasattr(p, "order_id"):   # SalesOrderRecord has order_id
        return p
      p = getattr(p, "parent", None)

    try:
      root = get_open_form().content
      if hasattr(root, "order_id"):
        return root
    except Exception:
      pass
    return None

  def _return_to_sales_order(self):
    """
    Standard return_to payload that lands back on this SalesOrderRecord and
    hints the UI to focus the Missing Routes region.
    """
    so_ctx = self._find_sales_order_context()
    so_id = getattr(so_ctx, "order_id", None)
    return {
      "form": "SalesOrderRecord",
      "kwargs": {"order_id": so_id, "focus": "missing_routes"},
      # SalesOrderRecord doesn't use list filters, but include empty for consistency
      "filters": None,
    }

  # ---- buttons ----
  def button_open_part_click(self, **e):
    pid = (self.item or {}).get("part_id")
    if not pid:
      Notification("No part_id on this row.", style="warning").show()
      return
    open_form("PartRecord", part_id=pid, return_to=self._return_to_sales_order())

  def button_open_ops_click(self, **e):
    pid = (self.item or {}).get("part_id")
    if not pid:
      Notification("No part_id on this row.", style="warning").show()
      return

    # Resolve route for this part
    try:
      p = anvil.server.call("get_part", pid) or {}
      route_id = (p.get("route_id") or "").strip()
      if not route_id:
        Notification("This part has no default route set. Choose a route in PartRecord first.", style="warning").show()
        return

      # Optional: resolve names for nicer headers
      part_name = p.get("description") or p.get("name") or pid
      try:
        r = anvil.server.call("routes_get", route_id) or {}
        route_name = r.get("name") or route_id
      except Exception:
        route_name = route_id

      open_form("PartRouteOps",
                part_id=pid,
                route_id=route_id,
                part_name=part_name,
                route_name=route_name,
                return_to=self._return_to_sales_order())

    except Exception as ex:
      alert(f"Could not open Part Operations: {ex}")


