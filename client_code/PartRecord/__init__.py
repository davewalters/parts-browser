from anvil import *
import anvil.server
from ._anvil_designer import PartRecordTemplate
from datetime import datetime
from .. import config
from .. PartRecords import PartRecords   # keep as-is if this is your working import

class PartRecord(PartRecordTemplate):
  def __init__(self, part_id,
               prev_filter_part="",
               prev_filter_desc="",
               prev_filter_type="",
               prev_filter_status="",
               prev_filter_designbom=False,
               **kwargs):
    self.init_components(**kwargs)

    # Roles
    self.button_save.role = "save-button"
    self.button_back.role = "mydefault-button"
    self.button_vendor_list.role = "mydefault-button"
    self.button_delete.role = "delete-button"
    self.button_BOM.role = "new-button"
    try:
      self.button_part_route_ops.role = "mydefault-button"
    except Exception:
      pass

    # Preserve list filters for back navigation
    self.prev_filter_part = prev_filter_part
    self.prev_filter_desc = prev_filter_desc
    self.prev_filter_type = prev_filter_type
    self.prev_filter_status = prev_filter_status
    self.prev_filter_designbom = prev_filter_designbom

    # ------- Route name <-> id maps (populated in _load_routes_dropdown) -------
    self._route_id_by_name = {}
    self._route_name_by_id = {}

    # Load part (if editing)
    self.part = {}
    self.is_new = part_id is None
    if not self.is_new:
      try:
        fetched = anvil.server.call("get_part", part_id)
        if fetched is None:
          Notification(f"⚠️ Part ID '{part_id}' not found in database.", style="warning").show()
        else:
          self.part = fetched
      except Exception as e:
        Notification(f"❌ Failed to load part: {e}", style="danger").show()

    # Dropdowns (static lists)
    self.drop_down_status.items = ["active", "obsolete"]
    self.drop_down_type.items = ["part", "assembly", "phantom", "material", "service", "documentation"]
    self.drop_down_unit.items = ["each", "per m", "per hr", "multiple"]
    self.drop_down_process.items = ["machine", "3DP", "assemble", "laser-cut", "weld", "cut-bend", "waterjet-cut", "-"]

    # Populate fields from part
    self.text_box_id.text = self.part.get("_id", "")
    self.text_box_rev.text = self.part.get("revision", "A")
    self.text_box_desc.text = self.part.get("description", "")
    self.drop_down_status.selected_value = self.part.get("status", "active")
    self.drop_down_type.selected_value = self.part.get("type", "part")
    self.drop_down_process.selected_value = self.part.get("process", "-")
    self.text_box_material.text = self.part.get("material_spec", "")
    self.drop_down_unit.selected_value = self.part.get("unit", "each")

    # Load routes and select current one (by id -> name)
    self._load_routes_dropdown()
    current_route_id = self.part.get("route_id", "")
    if current_route_id and current_route_id in self._route_name_by_id:
      self.drop_down_route_name.selected_value = self._route_name_by_id[current_route_id]
    else:
      self.drop_down_route_name.selected_value = None

    # Routing preview in header (server helper)
    try:
      if current_route_id:
        self.label_route_preview_value.text = anvil.server.call("routes_preview_string", current_route_id, 12) or ""
      else:
        self.label_route_preview_value.text = ""
    except Exception:
      self.label_route_preview_value.text = ""

    # Enable/disable Part Ops button based on validity of selection
    self._update_part_ops_button_enabled_state()

    # Vendor (resolve company name; default_vendor stays vendor_id internally)
    vid = self.part.get("default_vendor", "")
    if vid:
      try:
        vmap = anvil.server.call("get_vendor_names_by_ids", [vid]) or {}
        self.label_vendor.text = vmap.get(vid, vid)
      except Exception:
        self.label_vendor.text = vid
    else:
      self.label_vendor.text = "–"

    # Cost + sell price
    latest_cost = self.part.get("latest_cost", {}) or {}
    cost_nz = latest_cost.get("cost_nz", 0.0)
    cost_date = latest_cost.get("cost_date", datetime.today().isoformat())
    self.label_cost_nz.text = self.format_currency(cost_nz)
    self.label_date_costed.text = self.format_date(cost_date)

    # sell_price is always NZD
    sell_price_val = self.part.get("sell_price", 0.0)
    self.text_box_sell_price_nzd.text = self._format_price_field(sell_price_val)
    self.text_box_sell_price_nzd.set_event_handler("lost_focus", self._format_price_on_blur)

    # Buttons visibility
    self.button_delete.visible = bool(self.part)
    self.button_BOM.visible = self.drop_down_type.selected_value == "assembly"

  # ---------------------- Route dropdown loader ----------------------

  def _load_routes_dropdown(self):
    """
    Populate route name dropdown. We show names, but will save the corresponding route_id.
    """
    try:
      routes = anvil.server.call("routes_list", "") or []   # all routes (product_family filter blank)
      # Alternative: routes = anvil.server.call("get_filtered_routes_by_name", "", 1000) or []

      self._route_id_by_name = {}
      self._route_name_by_id = {}
      name_items = []
      for r in routes:
        rid = r.get("_id", "")
        rname = r.get("name", "")
        if not rid or not rname:
          continue
        self._route_id_by_name[rname] = rid
        self._route_name_by_id[rid] = rname
        name_items.append(rname)

      self.drop_down_route_name.items = sorted(name_items, key=lambda s: s.lower())
    except Exception as e:
      self.drop_down_route_name.items = []
      Notification(f"⚠️ Failed to load routes: {e}", style="warning").show()

  # ---------------------- Save ----------------------

  def button_save_click(self, **event_args):
    try:
      latest_cost = {
        "cost_nz": float(self.label_cost_nz.text.replace("$", "") or 0),
        "cost_date": self.label_date_costed.text.strip() or "1970-01-01"
      }

      sell_price_val = self._parse_price(self.text_box_sell_price_nzd.text)
      selected_route_name = self.drop_down_route_name.selected_value
      route_id_to_save = self._route_id_by_name.get(selected_route_name, "") if selected_route_name else ""

      new_data = {
        "_id": self.text_box_id.text,
        "description": self.text_box_desc.text,
        "revision": self.text_box_rev.text,
        "status": self.drop_down_status.selected_value,
        "default_vendor": self.part.get("default_vendor", ""),
        "type": self.drop_down_type.selected_value,
        "process": self.drop_down_process.selected_value,
        "material_spec": self.text_box_material.text,
        "unit": self.drop_down_unit.selected_value,
        "latest_cost": latest_cost,
        "group_code": self.part.get("group_code", ""),
        "root_serial": self.part.get("root_serial", ""),
        "variant": self.part.get("variant", ""),
        "vendor_part_numbers": self.part.get("vendor_part_numbers", []),
        "sell_price": sell_price_val,
        "sell_currency": "NZD",
        "route_id": route_id_to_save,
      }

      validated = anvil.server.call("save_part_from_client", new_data)
      self.part = validated

      Notification("✅ Part saved.", style="success").show()

    except Exception as e:
      Notification(f"❌ Save failed: {e}", style="danger").show()

  # ---------------------- Route dropdown change (auto-save + preview) ----------------------

  def drop_down_route_name_change(self, **event_args):
    """
    Project pattern: auto-save on change, then refresh preview and button state.
    """
    selected_route_name = self.drop_down_route_name.selected_value
    route_id_to_save = self._route_id_by_name.get(selected_route_name or "", "")

    # Save immediately
    try:
      latest_cost = {
        "cost_nz": float(self.label_cost_nz.text.replace("$", "") or 0),
        "cost_date": self.label_date_costed.text.strip() or "1970-01-01"
      }
      sell_price_val = self._parse_price(self.text_box_sell_price_nzd.text)

      new_data = {
        "_id": self.text_box_id.text,
        "description": self.text_box_desc.text,
        "revision": self.text_box_rev.text,
        "status": self.drop_down_status.selected_value,
        "default_vendor": self.part.get("default_vendor", ""),
        "type": self.drop_down_type.selected_value,
        "process": self.drop_down_process.selected_value,
        "material_spec": self.text_box_material.text,
        "unit": self.drop_down_unit.selected_value,
        "latest_cost": latest_cost,
        "group_code": self.part.get("group_code", ""),
        "root_serial": self.part.get("root_serial", ""),
        "variant": self.part.get("variant", ""),
        "vendor_part_numbers": self.part.get("vendor_part_numbers", []),
        "sell_price": sell_price_val,
        "sell_currency": "NZD",
        "route_id": route_id_to_save,
      }
      validated = anvil.server.call("save_part_from_client", new_data)
      self.part = validated

      # Update preview quietly
      try:
        if route_id_to_save:
          self.label_route_preview_value.text = anvil.server.call("routes_preview_string", route_id_to_save, 12) or ""
        else:
          self.label_route_preview_value.text = ""
      except Exception:
        self.label_route_preview_value.text = ""

      # Update Part Ops button enabled state
      self._update_part_ops_button_enabled_state()

    except Exception as e:
      Notification(f"⚠️ Could not save route: {e}", style="warning").show()
      # Keep previous state; user can retry/select again

  # ---------------------- Navigation ----------------------

  def button_back_click(self, **event_args):
    open_form("PartRecords",
              filter_part=self.prev_filter_part,
              filter_desc=self.prev_filter_desc,
              filter_type=self.prev_filter_type,
              filter_status=self.prev_filter_status,
              filter_designbom=self.prev_filter_designbom)

  def button_delete_click(self, **event_args):
    part_id = self.text_box_id.text
    if confirm(f"Are you sure you want to delete part '{part_id}'?"):
      try:
        response = anvil.server.call("delete_part", part_id)
        if response.get("deleted_count", 0) == 1:
          Notification("🗑️ Part deleted.", style="danger").show()
        else:
          Notification(f"⚠️ Part '{part_id}' not found.", style="warning").show()
        get_open_form().content = PartRecords(filter_part=self.prev_filter_part, filter_desc=self.prev_filter_desc)
      except Exception as e:
        Notification(f"❌ Delete failed: {e}", style="danger").show()

  def button_vendor_list_click(self, **event_args):
    part_id = self.ensure_part_saved()
    if part_id:
      open_form("PartVendorRecords",
                part_id=part_id,
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status,
                prev_filter_designbom=self.prev_filter_designbom)

  def button_BOM_click(self, **event_args):
    part_id = self.ensure_part_saved()
    if part_id:
      open_form("DesignBOMRecord",
                assembly_part_id=part_id,
                prev_filter_part=self.prev_filter_part,
                prev_filter_desc=self.prev_filter_desc,
                prev_filter_type=self.prev_filter_type,
                prev_filter_status=self.prev_filter_status,
                prev_filter_designbom=self.prev_filter_designbom)

  def button_part_route_ops_click(self, **event_args):
    part_id = self.ensure_part_saved()
    #print("PartRecord: part_id:", part_id)
    if not part_id:
      return
  
    selected_route_name = self.drop_down_route_name.selected_value
    #print("PartRecord: selected_route_name:", selected_route_name)
    if not selected_route_name:
      Notification("Select a Route before opening Part Operations.", style="warning").show()
      return
  
    route_id = self._route_id_by_name.get(selected_route_name or "", "")
    #print("PartRecord: route_id:", route_id)
    if not route_id:
      Notification("Selected Route name could not be resolved to an ID.", style="warning").show()
      return
  
    try:
      # IMPORTANT: import the class, construct it, then open it.
      from ..PartRouteOps import PartRouteOps
      #print("PartRecord: opening PartRouteOps with",
      #      dict(part_id=part_id, route_id=route_id,
      #          part_name=self.text_box_desc.text or part_id,
      #          route_name=selected_route_name))
  
      frm = PartRouteOps(
        part_id=part_id,
        route_id=route_id,
        part_name=self.text_box_desc.text or part_id,
        route_name=selected_route_name,
      )
      open_form(frm)
  
    except Exception as e:
      #print("💥 PartRouteOps open failed:", e)
      alert(f"Couldn't open Part Operations:\n{e}")
      open_form("Nav")


  # ---------------------- Helpers ----------------------

  def _update_part_ops_button_enabled_state(self):
    selected_route_name = self.drop_down_route_name.selected_value
    route_id = self._route_id_by_name.get(selected_route_name or "", "")
    self.button_part_route_ops.enabled = bool(route_id)

  def format_date(self, iso_string):
    if not iso_string or not isinstance(iso_string, str):
      return "1970-01-01"
    return iso_string.split("T")[0] if "T" in iso_string else iso_string

  def format_currency(self, value):
    try:
      return f"${float(value):.2f}"
    except (ValueError, TypeError):
      return "–"

  def _parse_price(self, s) -> float:
    try:
      return float((s or "").replace("$", "").replace(",", "").strip() or 0.0)
    except Exception:
      return 0.0

  def _format_price_field(self, value) -> str:
    try:
      return f"{float(value):.2f}"
    except Exception:
      return "0.00"

  def _format_price_on_blur(self, **e):
    self.text_box_sell_price_nzd.text = self._format_price_field(self.text_box_sell_price_nzd.text)

  def ensure_part_saved(self):
    part_id = self.part.get("_id")
    if not part_id:
      self.button_save_click()
      part_id = self.part.get("_id")
    return part_id






