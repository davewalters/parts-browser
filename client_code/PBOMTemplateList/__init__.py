from anvil import *
import anvil.server

class PBOMTemplateList(PBOMTemplateListTemplate):
  def __init__(self,
               filter_parent_prefix="",
               filter_status="",
               filter_rev="",
               filter_plant="",
               **kwargs):
    self.init_components(**kwargs)

    # Previous filter state for navigation
    self.prev_filter_parent_prefix = filter_parent_prefix or ""
    self.prev_filter_status = filter_status or ""
    self.prev_filter_rev = filter_rev or ""
    self.prev_filter_plant = filter_plant or ""

    # Initialise UI controls
    self.text_parent_prefix.text = self.prev_filter_parent_prefix
    self.drop_down_status.items = ["", "draft", "active", "obsolete", "archived"]
    self.drop_down_status.selected_value = self.prev_filter_status
    self.text_rev.text = self.prev_filter_rev
    self.text_plant.text = self.prev_filter_plant

    # Event wiring for update-on-change pattern
    self.text_parent_prefix.set_event_handler("pressed_enter", self.update_filter)
    self.text_rev.set_event_handler("pressed_enter", self.update_filter)
    self.text_plant.set_event_handler("pressed_enter", self.update_filter)
    self.drop_down_status.set_event_handler("change", self.update_filter)

    self.repeating_panel_pbomtpl.set_event_handler("x-open-detail", self.open_detail)

    self._last = None
    self.update_filter()

  def update_filter(self, **event_args):
    self.prev_filter_parent_prefix = self.text_parent_prefix.text or ""
    self.prev_filter_status = self.drop_down_status.selected_value or ""
    self.prev_filter_rev = self.text_rev.text or ""
    self.prev_filter_plant = self.text_plant.text or ""

    q = (self.prev_filter_parent_prefix,
         self.prev_filter_status,
         self.prev_filter_rev,
         self.prev_filter_plant)

    if q == self._last:
      return
    self._last = q

    try:
      rows = anvil.server.call("pbomtpl_search",
                               parent_prefix=self.prev_filter_parent_prefix,
                               status=self.prev_filter_status,
                               rev=self.prev_filter_rev,
                               plant_id=self.prev_filter_plant,
                               limit=300)
      self.repeating_panel_pbomtpl.items = rows or []
      self.label_count.text = f"{len(rows or [])} PBOM templates"
    except Exception as e:
      self.label_count.text = f"Error: {e}"
      self.repeating_panel_pbomtpl.items = []

  def open_detail(self, row, **event_args):
    open_form("PBOMTemplateRecord",
              pbom_id=row["_id"],
              parent_prefix=self.prev_filter_parent_prefix,
              status=self.prev_filter_status,
              rev=self.prev_filter_rev,
              plant=self.prev_filter_plant)

