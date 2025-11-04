from anvil import *
import anvil.server

from ._anvil_designer import DesignBOMRecordTemplate
from .DesignBOMRow import DesignBOMRow
from ..PartRecords import PartRecords

class DesignBOMRecord(DesignBOMRecordTemplate):
  def __init__(self, assembly_part_id,
               prev_filter_part="",
               prev_filter_desc="",
               prev_filter_type="",
               prev_filter_status="",
               prev_filter_designbom=False,
               return_to: dict | None = None,
               **kwargs):
    self.init_components(**kwargs)
    self._return_to = return_to or None
    self.part_cache = {}
    self.assembly_part_id = assembly_part_id
    self.label_assembly_id.text = self.assembly_part_id
    self.button_add_row.role = "new-button"
    self.button_save_bom.role = "save-button"

    self.prev_filter_part = prev_filter_part
    self.prev_filter_desc = prev_filter_desc
    self.prev_filter_type = prev_filter_type
    self.prev_filter_status = prev_filter_status
    self.prev_filter_designbom=prev_filter_designbom

    self.repeating_panel_1.role = "scrolling-panel"
    self.repeating_panel_1.set_event_handler("x-validation-updated", self.validate_all_rows)
    self.repeating_panel_1.set_event_handler("x-remove-row", self.remove_row)
    self.repeating_panel_1.set_event_handler("x-edit-vendor", self.edit_vendor_for_row)

    self.load_existing_bom()

  def load_existing_bom(self):
    self.button_save_bom.enabled = False
    bom_doc = anvil.server.call('get_design_bom', self.assembly_part_id)
    self.bom_rows = bom_doc.get("components", [])
    self.repeating_panel_1.items = self.bom_rows
    self.label_cost_status.text = ""
  
    try:
      assembly_part = anvil.server.call("get_part", self.assembly_part_id)
      latest_cost = assembly_part.get("latest_cost", {})
      cost_nz = latest_cost.get("cost_nz", None)
      self.label_assembly_cost_nz.text = self.format_currency(cost_nz)
    except Exception as e:
      self.label_assembly_cost_nz.text = "–"
      Notification(f"⚠️ Could not load cost: {e}", style="warning").show()


  def validate_all_rows(self, **event_args):
    #print("🚨 validate_all_rows called")
    all_valid = all(row.item.get("is_valid_part", False) for row in self.repeating_panel_1.get_components())
    self.button_save_bom.enabled = all_valid

  def button_add_row_click(self, **event_args):
    # Retain full data from existing rows
    updated_bom = []
    for row in self.repeating_panel_1.get_components():
      item_copy = row.item.copy()
      # Ensure qty is updated to what's currently typed in
      try:
        item_copy["qty"] = float(row.text_box_qty.text.strip())
      except (ValueError, TypeError):
        item_copy["qty"] = 0
      item_copy["part_id"] = row.text_box_part_id.text.strip()
      updated_bom.append(item_copy)

    # Insert a new blank row at the top
    updated_bom.insert(0, {"part_id": "", "qty": 1})

    self.bom_rows = updated_bom
    self.repeating_panel_1.items = self.bom_rows

  def button_save_bom_click(self, **event_args):
    self.label_cost_status.text = "Saving and rolling up cost..."
    self.button_save_bom.enabled = False

    try:
      result = anvil.server.call(
        'save_design_bom_and_rollup',
        self.assembly_part_id,
        self.repeating_panel_1.items
      )

      cost = result["cost_nz"]
      self.label_assembly_cost_nz.text = self.format_currency(cost)
      skipped = result["skipped_parts"]
      msg = f"✅ Cost updated: ${cost:.2f}"
      if skipped:
        msg += f" — {len(skipped)} skipped"
      self.label_cost_status.text = msg

    except Exception as e:
      self.label_cost_status.text = f"❌ Error: {str(e)}"

    finally:
      self.button_save_bom.enabled = True

  def edit_vendor_for_row(self, part_id=None, **event_args):
    #print(f"edit_vendor_for_row called: {part_id}")
    if part_id:
      open_form("PartVendorRecords",
                part_id=part_id,
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status,
                prev_filter_designbom=self.prev_filter_designbom,
                back_to_bom=True,
                assembly_part_id=self.assembly_part_id)

  def remove_row(self, **event_args):
    row_to_remove = event_args['row']
    updated_bom = []

    for row in self.repeating_panel_1.get_components():
      if row is not row_to_remove:
        item_copy = row.item.copy()
        try:
          item_copy["qty"] = float(row.text_box_qty.text.strip())
        except (ValueError, TypeError):
          item_copy["qty"] = 0
        item_copy["part_id"] = row.text_box_part_id.text.strip()
        updated_bom.append(item_copy)

    self.bom_rows = updated_bom
    self.repeating_panel_1.items = self.bom_rows

  def _go_back(self):
    if self._return_to:
      try:
        form_name = self._return_to.get("form") or "PartRecords"
        kwargs = dict(self._return_to.get("kwargs") or {})
        return_filters = self._return_to.get("filters")
        open_form(form_name, **kwargs, return_filters=return_filters)
        return
      except Exception as ex:
        Notification(f"Back navigation failed: {ex}", style="warning").show()

    # Fallback to PartRecords with your preserved filters
    open_form("PartRecords",
              filter_part=self.prev_filter_part,
              filter_desc=self.prev_filter_desc,
              filter_type=self.prev_filter_type,
              filter_status=self.prev_filter_status,
              filter_designbom=self.prev_filter_designbom)
  
  def button_back_click(self, **event_args):
    self._go_back()

  def format_currency(self, value):
    """Format a float as NZ currency, or return '–' if invalid."""
    try:
      return f"${float(value):.2f}"
    except (ValueError, TypeError):
      return "–"








