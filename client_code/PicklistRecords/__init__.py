# client_code/PicklistRecords/__init__.py
from anvil import *
import anvil.server
from ._anvil_designer import PicklistRecordsTemplate
#from ..PicklistRecordsRow import PicklistRecordsRow

class PicklistRecords(PicklistRecordsTemplate):
  def __init__(self, filter_sales_order_id: str = "", filter_work_order_id: str = "", **kwargs):
    self.init_components(**kwargs)

    # Controls / roles
    self.drop_down_status.items = ["", "ready", "in_progress", "attention"]
    self.drop_down_status.selected_value = ""
    #self.button_apply.role = "mydefault-button"
    self.button_newest.role = "new-button"

    # Default filters
    self.text_sales_order_id.text = filter_sales_order_id or ""
    self.text_work_order_id.text = filter_work_order_id or ""
    self.text_bin_id.text = ""

    # Repeating panel
    self.repeating_panel_picklists.item_template = PicklistRecordsRow
    self.repeating_panel_picklists.set_event_handler("x-open", self._open_detail)

    # --- Wire events to our standard update-on-change pattern ---
    # Text boxes: on Enter & Change
    self.text_sales_order_id.set_event_handler('pressed_enter', self.update_filter)
    self.text_sales_order_id.set_event_handler('change',        self.update_filter)
    self.text_work_order_id.set_event_handler('pressed_enter',  self.update_filter)
    self.text_work_order_id.set_event_handler('change',         self.update_filter)
    self.text_bin_id.set_event_handler('pressed_enter',         self.update_filter)
    self.text_bin_id.set_event_handler('change',                self.update_filter)

    # Dropdowns / Dates: on Change
    self.drop_down_status.set_event_handler('change', self.update_filter)
    self.date_from.set_event_handler('change',        self.update_filter)
    self.date_to.set_event_handler('change',          self.update_filter)

    # Buttons also call update_filter for convenience
    #self.button_apply.set_event_handler('click',  self.update_filter)
    self.button_newest.set_event_handler('click', self._quick_last_7d)

    # Initial load
    self.update_filter()

  # ---------- Helpers ----------
  def _coerce_date(self, d):
    # Anvil DatePicker has .date (datetime.date or None); also tolerate empty strings
    try:
      return d.date if hasattr(d, "date") else None
    except Exception:
      return None

  def _quick_last_7d(self, **event_args):
    import datetime as _dt
    today = _dt.date.today()
    self.date_from.date = today - _dt.timedelta(days=7)
    self.date_to.date = today
    self.update_filter()

  # ---------- Main filter apply ----------
  def update_filter(self, **event_args):
    so = (self.text_sales_order_id.text or "").strip()
    wo = (self.text_work_order_id.text or "").strip()
    bn = (self.text_bin_id.text or "").strip()
    st = (self.drop_down_status.selected_value or "").strip()
    fd = self._coerce_date(self.date_from)   # datetime.date or None
    td = self._coerce_date(self.date_to)     # datetime.date or None

    try:
      data = anvil.server.call(
        "picklist_list_advanced",
        sales_order_id=so,
        work_order_id=wo,
        bin_id=bn,
        status=st,
        from_date=fd,
        to_date=td,
        limit=500
      ) or []
      self.repeating_panel_picklists.items = data
      self.label_count.text = f"{len(data)} picklists"
    except Exception as ex:
      self.repeating_panel_picklists.items = []
      self.label_count.text = f"Error: {ex}"

  # ---------- Navigation ----------
  def _open_detail(self, picklist_id: str, **event_args):
    try:
      from ..PicklistRecord import PicklistRecord
      open_form("PicklistRecord", picklist_id=picklist_id)
    except Exception:
      open_form("Nav")

