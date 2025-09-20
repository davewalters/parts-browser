from anvil import *
import anvil.server
from ._anvil_designer import WorkOrderRecordTemplate
from ..WorkOrderRouteRow import WorkOrderRouteRow
from ..WorkOrderMaterialRow import WorkOrderMaterialRow

class WorkOrderRecord(WorkOrderRecordTemplate):
  def __init__(self, wo_id: str, is_new: bool = False, **kwargs):
    self.init_components(**kwargs)
    self.wo_id = wo_id
    self.is_new = bool(is_new)
    self._created = False
    self._tpl_qty_per = {}   # PBOM qty_per by part_id
    self._wo_qty = 1

    # Header widgets setup
    self.drop_down_status.items = ["planned", "released", "complete", "closed"]
    self.button_back.role = "mydefault-button"

    # Event wiring for update-on-change
    for tb in (self.text_part_id, self.text_qty, self.text_due_date, self.text_sales_order_id):
      tb.set_event_handler('pressed_enter', self._header_field_changed)
      tb.set_event_handler('change', self._header_field_changed)
    self.drop_down_status.set_event_handler('change', self._status_changed)

    # Panels
    self.repeating_panel_route.item_template = WorkOrderRouteRow
    self.repeating_panel_materials.item_template = WorkOrderMaterialRow
    self.repeating_panel_materials.set_event_handler("x-row-changed", self._reload_materials)

    # Add component
    self.button_add_component.role = "save-button"
    self.button_add_component.set_event_handler('click', self._add_component)

    self._load_initial()

  # ---------- initial load ----------
  def _load_initial(self):
    self.label_wo_id.text = self.wo_id
    if self.is_new:
      # New mode: nothing in DB yet; let user fill header, then we create on-the-fly
      self.label_part_id_value.text = ""
      self.text_part_id.text = ""
      self.text_qty.text = "1"
      self.text_due_date.text = ""
      self.text_sales_order_id.text = ""
      self.drop_down_status.selected_value = "planned"
      # Hide tabs until created
      self.repeating_panel_route.items = []
      self.repeating_panel_materials.items = []
      self.label_materials_count.text = ""
    else:
      self._load_existing()

  def _load_existing(self):
    wo = anvil.server.call("wo_get", self.wo_id) or {}
    self._created = bool(wo)
    self.is_new = not self._created

    # Header
    self.label_part_id_value.text = wo.get("part_id","")
    self.text_part_id.text = wo.get("part_id","")  # allow change post-creation only if you want; typically you don’t
    self.text_qty.text = str(wo.get("qty",""))
    self._wo_qty = int(wo.get("qty") or 1)
    self.text_due_date.text = str(wo.get("due_date",""))
    self.text_sales_order_id.text = wo.get("sales_order_id","") or ""
    self.drop_down_status.selected_value = wo.get("status","planned")

    # Routing (snapshot)
    route_ops = list(wo.get("route_ops") or [])
    try:
      id_to_name = anvil.server.call("get_cell_id_to_name_map") or {}
    except Exception:
      id_to_name = {}
    r_items = []
    for op in route_ops:
      r_items.append({
        "seq": op.get("seq"),
        "cell_id": op.get("cell_id",""),
        "cell_name": id_to_name.get(op.get("cell_id"), op.get("cell_id","")),
        "operation_name": op.get("operation_name",""),
        "cycle_min_per_unit": op.get("cycle_min_per_unit", 0.0),
      })
    self.repeating_panel_route.items = r_items

    # PBOM baseline for labels
    self._tpl_qty_per = {}
    try:
      tpl = anvil.server.call("pbom_get_active_for_part", wo.get("part_id"))
      if tpl and tpl.get("lines"):
        for ln in tpl["lines"]:
          pid = ln.get("part_id"); 
          if not pid: 
            continue
          try:
            self._tpl_qty_per[pid] = float(ln.get("qty_per", 0.0) or 0.0)
          except Exception:
            self._tpl_qty_per[pid] = 0.0
    except Exception:
      pass

    # Materials
    self._reload_materials()

  def _reload_materials(self, **e):
    if not self._created:
      self.repeating_panel_materials.items = []
      self.label_materials_count.text = ""
      return
    mats = anvil.server.call("wobom_get_lines", self.wo_id) or []
    view = []
    for m in mats:
      pid = m.get("part_id")
      pbom_qty = None
      if pid in self._tpl_qty_per:
        pbom_qty = self._tpl_qty_per[pid] * self._wo_qty
      view.append({
        "_doc": dict(m),
        "part_id": pid,
        "desc": m.get("desc",""),
        "unit": m.get("unit",""),
        "qty_required": m.get("qty_required", 0.0),
        "pbom_qty": pbom_qty,
        "is_manual": bool(m.get("is_manual", False)),
      })
    self.repeating_panel_materials.items = view
    self.label_materials_count.text = f"{len(view)} material lines"

  # ---------- header change handling ----------
  def _header_field_changed(self, **e):
    part_id = (self.text_part_id.text or "").strip()
    qty_text = (self.text_qty.text or "").strip()
    due = (self.text_due_date.text or "").strip()
    so = (self.text_sales_order_id.text or "").strip() or None

    # In "new" mode: create once all required fields are valid
    if not self._created:
      # Validate basic
      if not part_id or not due:
        return
      try:
        qty = int(qty_text)
        if qty <= 0:
          return
      except Exception:
        return
      # Create with snapshots
      try:
        payload = {
          "_id": self.wo_id,
          "part_id": part_id,
          "qty": int(qty),
          "due_date": due,
          "sales_order_id": so,
        }
        anvil.server.call("wo_create_with_snapshots", payload)
        self._created = True
        # Reload into existing mode
        self._load_existing()
        Notification("Work order created.", style="success").show()
      except Exception as ex:
        alert(f"Create failed: {ex}")
      return

    # Existing: apply shallow updates immediately
    updates = {}
    # (Allow qty & due date & SO to change; typically part_id stays fixed after creation)
    try:
      q = int(qty_text)
      if q > 0 and q != self._wo_qty:
        updates["qty"] = q
    except Exception:
      pass
    if due:
      updates["due_date"] = due
    updates["sales_order_id"] = so

    if updates:
      try:
        anvil.server.call("wo_update", self.wo_id, updates)
        if "qty" in updates:
          self._wo_qty = updates["qty"]
        Notification("Updated.", style="success").show()
        # Reload materials to refresh PBOM*qty labels if qty changed
        if "qty" in updates:
          self._reload_materials()
      except Exception as ex:
        alert(f"Update failed: {ex}")

  def _status_changed(self, **e):
    if not self._created:
      # Keep 'planned' visible; won’t transition until created
      self.drop_down_status.selected_value = "planned"
      return
    try:
      st = self.drop_down_status.selected_value
      anvil.server.call("wo_set_status", self.wo_id, st)
      Notification("Status updated.", style="success").show()
      self._load_existing()
    except Exception as ex:
      alert(f"Status change failed: {ex}")

  def _add_component(self, **e):
    if not self._created:
      Notification("Create the work order first (enter part, qty, due).").show()
      return
    pid = (self.text_add_part_id.text or "").strip()
    qty_s = (self.text_add_qty.text or "").strip()
    if not pid or not qty_s:
      Notification("Part and qty required.").show(); return
    try:
      qty = float(qty_s)
      if qty <= 0:
        Notification("Qty must be > 0.").show(); return
    except Exception:
      Notification("Qty must be numeric.").show(); return

    try:
      pdoc = anvil.server.call("parts_get", pid) or {}
    except Exception:
      pdoc = {}
    desc = pdoc.get("description","")
    unit = pdoc.get("unit","")

    doc = {
      "wo_id": self.wo_id,
      "part_id": pid,
      "desc": desc,
      "unit": unit,
      "qty_required": qty,
      "operation_seq": 0,
      "lot_traced": False,
      "serial_required": False,
      "reservations": [],
      "serials": [],
      "anchor_part_id": self.text_part_id.text or self.label_part_id_value.text,
      "is_manual": True,
    }
    try:
      anvil.server.call("wobom_insert_line", doc)
      self.text_add_part_id.text = ""
      self.text_add_qty.text = ""
      self._reload_materials()
      Notification("Component added.", style="success").show()
    except Exception as ex:
      alert(f"Add failed: {ex}")

  def button_back_click(self, **e):
    try:
      from ..WorkOrderRecords import WorkOrderRecords
      open_form("WorkOrderRecords")
    except Exception:
      open_form("Nav")
