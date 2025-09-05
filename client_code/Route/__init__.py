# client_code/Route/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import RouteTemplate
from ..RouteRow import RouteRow

class Route(RouteTemplate):
  def __init__(self, filter_route_name: str = "", **kwargs):
    self.init_components(**kwargs)

    self.button_new_route.role = "new-button"

    self.prev_filter_route_name = filter_route_name or ""
    self.text_filter_route_name.text = self.prev_filter_route_name

    self.repeating_panel_routes.item_template = RouteRow
    self._load_routes()

  def _load_routes(self):
    name_substring = self.text_filter_route_name.text or ""
    routes = anvil.server.call("get_filtered_routes", route_name=name_substring)
    routes = sorted(routes, key=lambda r: (r.get("route_name") or "").lower())
    self.repeating_panel_routes.items = routes

  def text_filter_route_name_pressed_enter(self, **event_args):
    self.prev_filter_route_name = self.text_filter_route_name.text or ""
    self._load_routes()

  def button_new_route_click(self, **event_args):
    from ..RouteDetails import RouteDetails
    open_form("RouteDetails",
              route_id=None,
              prev_filter_route_name=self.text_filter_route_name.text or "")

