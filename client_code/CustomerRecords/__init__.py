from anvil import *
import anvil.server
from ._anvil_designer import CustomerRecordsTemplate

class CustomerRecords(CustomerRecordsTemplate):
  def __init__(self, name_filter: str = "", **properties):
    self.init_components(**properties)

    self.button_add_customer.role = "new-button"
    self.button_home.role = "mydefault-button"
    self.text_box_name_filter.text = name_filter or ""
    self.text_box_name_filter.set_event_handler("pressed_enter", self.update_filter)
    self.text_box_name_filter.set_event_handler("lost_focus", self.update_filter)

    # Initial load
    self._load_data()

  # ---- UI events ----
  def update_filter(self, **event_args):
    """Called on pressed_enter or lost_focus of the name filter."""
    self._load_data()

  def button_add_customer_click(self, **event_args):
    open_form("CustomerRecord",is_new=True)

  def button_home_click(self, **event_args):
    open_form("Nav")

  # ---- Data ----
  def _load_data(self):
    name_sub = (self.text_box_name_filter.text or "").strip()
    rows = anvil.server.call("list_customers_by_name", name_sub)
    self.label_count.text = f"{len(rows)} customer(s) returned"
    self.repeating_panel_customers.items = rows

