from anvil import *
import anvil.server
from ._anvil_designer import PBOMTemplateListTemplate

class PBOMTemplateList(PBOMTemplateListTemplate):
  def __init__(self,
               filter_parent_prefix="",
               filter_status="",
               filter_rev="",
               filter_plant="",
               **kwargs):
    self.init_components(**kwargs)
    self.button_home.role = "mydefault-button"
    self.button_new_pbom.role = "new-button"

    # Persisted filter state
    self.prev_filter_parent_prefix = filter_parent_prefix or ""
    self.prev_filter_status = filter_status or ""
    self.prev_filter_rev = filter_rev or ""
    self.prev_filter_plant = filter_plant or ""

    # Initialise controls
    self.text_parent_prefix.text = self.prev_filter_parent_prefix
    self.drop_down_status.items = ["", "draft", "active", "obsolete", "archived"]
    self.drop_down_status.selected_value = self.prev_filter_status
    self.text_rev.text = self.prev_filter_rev
    self.text_plant.text = self.prev_filter_plant

    # Update-on-enter / change (as per project convention)
    self.text_parent_prefix.set_event_handler("pressed_enter", self.update_filter)
    self.text_rev.set_event_handler("pressed_enter", self.update_filter)
    self.text_plant.set_event_handler("pressed_enter", self.update_filter)
    self.drop_down_status.set_event_handler("change", self.update_filter)

    # Row open-detail event
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
      rows = anvil.server.call(
        "pbomtpl_search",
        parent_prefix=self.prev_filter_parent_prefix,
        status=self.prev_filter_status,
        rev=self.prev_filter_rev,
        plant_id=self.prev_filter_plant,
        limit=300
      ) or []
      self.repeating_panel_pbomtpl.items = rows
      self.label_count.text = f"{len(rows)} PBOM templates"
    except Exception as e:
      self.label_count.text = f"Error: {e}"
      self.repeating_panel_pbomtpl.items = []

  def button_new_pbom_click(self, **event_args):
    """
    New flow:
    - Simply open PBOMTemplateRecord with no pbom_id (blank header).
    - User enters parent_id in the record form; dependent fields populate on enter.
    """
    open_form("PBOMTemplateRecord",
              pbom_id=None,
              parent_prefix=self.prev_filter_parent_prefix,
              status=self.prev_filter_status,
              rev=self.prev_filter_rev,
              plant=self.prev_filter_plant)

  def open_detail(self, row, **event_args):
    open_form("PBOMTemplateRecord",
              pbom_id=row["_id"],
              parent_prefix=self.prev_filter_parent_prefix,
              status=self.prev_filter_status,
              rev=self.prev_filter_rev,
              plant=self.prev_filter_plant)

  # --------- Navigation --------
  def button_home_click(self, **event_args):
    open_form("Nav")



