from anvil import *
import anvil.server
from ._anvil_designer import PurchaseOrderRecordsTemplate
from datetime import datetime, date

class PurchaseOrderRecords(PurchaseOrderRecordsTemplate):
  def __init__(self, 
               filter_vendor="", 
               filter_part="", 
               filter_status="", 
               filter_from_date=None, 
               filter_to_date=None,
               filter_overdue=False,
               **kwargs):

    self.init_components(**kwargs)
    self.button_home.role = "mydefault-button"
    self.button_new_po.role = "new-button"
    self.repeating_panel_orders.role = "scrolling-panel"

    self.prev_filter_vendor = filter_vendor
    self.prev_filter_part = filter_part
    self.prev_filter_status = filter_status
    self.prev_filter_from_date = filter_from_date
    self.prev_filter_to_date = filter_to_date
    self.prev_filter_overdue = filter_overdue

    self.text_box_part.text = filter_part
    self.drop_down_status.items = ["", "open", "partial", "closed", "cancelled"]
    self.drop_down_status.selected_value = filter_status

    self.date_picker_from.date = filter_from_date
    self.date_picker_to.date = filter_to_date

    self.vendors = anvil.server.call("get_filtered_vendors")
    self.drop_down_vendor.items = [""] + [(v["company_name"], v["_id"]) for v in self.vendors]
    self.drop_down_vendor.selected_value = filter_vendor

    self.check_box_overdue_only.checked = filter_overdue

    self.drop_down_vendor.set_event_handler("change", self.update_filter)
    self.text_box_part.set_event_handler("change", self.update_filter)
    self.drop_down_status.set_event_handler("change", self.update_filter)
    self.date_picker_from.set_event_handler("change", self.update_filter)
    self.date_picker_to.set_event_handler("change", self.update_filter)
    self.check_box_overdue_only.set_event_handler("change", self.update_filter)
    self.repeating_panel_orders.set_event_handler("x-show-detail", self.show_detail)

    self.update_filter()

  def update_filter(self, **event_args):
    self.prev_filter_vendor = self.drop_down_vendor.selected_value or ""
    self.prev_filter_part = self.text_box_part.text or ""
    self.prev_filter_status = self.drop_down_status.selected_value or ""
    self.prev_filter_from_date = self.date_picker_from.date
    self.prev_filter_to_date = self.date_picker_to.date
    self.prev_filter_overdue = self.check_box_overdue_only.checked

    try:
      results = anvil.server.call("get_filtered_purchase_orders",
                                  vendor_id=self.prev_filter_vendor,
                                  part_contains=self.prev_filter_part,
                                  status=self.prev_filter_status,
                                  from_date=self.prev_filter_from_date,
                                  to_date=self.prev_filter_to_date
                                 )

      today = date.today()
      if self.prev_filter_overdue:
        def safe_date(d):
          if isinstance(d, str):
            try:
              return datetime.fromisoformat(d).date()
            except ValueError:
              return None
          return d

        results = [
          po for po in results
          if po.get("status") in ("open", "partial") and safe_date(po.get("due_date")) and safe_date(po["due_date"]) < today
        ]

      self.repeating_panel_orders.items = results
      self.label_count.text = f"{len(results)} purchase orders returned"
    except Exception as e:
      self.label_count.text = f"Error: {e}"
      self.repeating_panel_orders.items = []

  def show_detail(self, po, **event_args):
    open_form("PurchaseOrderRecord",
              purchase_order_id=po["_id"],
              filter_vendor=self.prev_filter_vendor,
              filter_part=self.prev_filter_part,
              filter_status=self.prev_filter_status,
              filter_from_date=self.prev_filter_from_date,
              filter_to_date=self.prev_filter_to_date,
              filter_overdue=self.prev_filter_overdue)

  def button_new_po_click(self, **event_args):
    open_form("PurchaseOrderRecord",
              purchase_order_id=None,
              filter_vendor=self.prev_filter_vendor,
              filter_part=self.prev_filter_part,
              filter_status=self.prev_filter_status,
              filter_from_date=self.prev_filter_from_date,
              filter_to_date=self.prev_filter_to_date,
              filter_overdue=self.prev_filter_overdue)

  def button_home_click(self, **event_args):
    open_form("Nav")


