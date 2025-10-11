# client_code/Route/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import RoutesTemplate
from .RouteRow import RouteRow   # <-- import the Form class, not the module

class Routes(RoutesTemplate):
  def __init__(self, filter_name: str = "", **kwargs):
    self.init_components(**kwargs)
    self.button_new_route.role = "new-button"
    self.button_back.role = "mydefault-button"
    self.repeating_panel_routes.role = "scrolling-panel"

    self.prev_filter_name = filter_name or ""
    self.text_filter_name.text = self.prev_filter_name

    # Use the actual class (or: self.repeating_panel_routes.item_template = "RouteRow")
    #self.repeating_panel_routes.item_template = RouteRow

    # Preload cell name map for previews
    self.cell_id_to_name = anvil.server.call("get_cell_id_to_name_map") or {}
    self._load_routes()

  def _load_routes(self):
    name_substring = self.text_filter_name.text or ""
    rows = anvil.server.call("get_filtered_routes_by_name",
                             route_name_substring=name_substring, limit=300) or []
    for r in rows:
      r["_cell_id_to_name"] = self.cell_id_to_name
    self.repeating_panel_routes.items = rows

  def text_filter_name_pressed_enter(self, **event_args):
    self.prev_filter_name = self.text_filter_name.text or ""
    self._load_routes()

  def button_new_route_click(self, **event_args):
    open_form("RouteDetails", route_id=None, prev_filter_name=self.text_filter_name.text or "")

  def button_back_click(self, **e):
    open_form("Nav")



