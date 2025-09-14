# client_code/Route/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import RoutesTemplate
from ..RouteRow import RouteRow

class Routes(RoutesTemplate):
  def __init__(self, filter_name: str = "", **kwargs):
    self.init_components(**kwargs)
    self.button_new_route.role = "new-button"
    self.button_back.role = "mydefault-button"
    self.repeating_panel_routes.role = "scrolling-panel"
    self.prev_filter_name = filter_name or ""
    self.text_filter_name.text = self.prev_filter_name
    self.repeating_panel_routes.item_template = RouteRow

    # Get cell name map once (for readable preview)
    self.cell_id_to_name = anvil.server.call("get_cell_id_to_name_map") or {}
    self._load_routes()

  def _load_routes(self):
    name_substring = self.text_filter_name.text or ""
    routes = anvil.server.call("get_filtered_routes_by_name", route_name_substring=name_substring, limit=300) or []
    # Store the map on each row item for preview composition
    for r in routes:
      r["_cell_id_to_name"] = self.cell_id_to_name
    self.repeating_panel_routes.items = routes

  def text_filter_name_pressed_enter(self, **event_args):
    self.prev_filter_name = self.text_filter_name.text or ""
    self._load_routes()

  def button_new_route_click(self, **event_args):
    from ..RouteDetails import RouteDetails
    open_form("RouteDetails", route_id=None, prev_filter_name=self.text_filter_name.text or "")

  def button_back_click(self, **e):
    open_form("Nav")


