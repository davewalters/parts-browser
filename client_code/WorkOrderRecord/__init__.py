from anvil import *
import anvil.server
from ._anvil_designer import WorkOrderRecordTemplate
from ..WorkOrderRouteRow import WorkOrderRouteRow
from ..WorkOrderMaterialRow import WorkOrderMaterialRow
from datetime import date, datetime

class WorkOrderRecord(WorkOrderRecordTemplate):
  def __init__(self, wo_id: str, is_new: bool = False, **kwargs):
    self.init_components(**kwargs)
    self.wo_id = wo_id
    self.is_new = bool(is_new)
    self._created = False
    self._tpl_qty_per = {}   # PBOM qty_per by part_id
    self._wo_qty = 1
    self._route_steps = []          # list of {"seq": int, "cell_id": str}
    self._seq_to_cell_id = {}       # {seq: cell_id}

    # Header widgets setup
    self.drop_down_status.items = ["planned","released","wip","complete","closed"]
    self.button_back.role = "mydefault-button"

    # Event wiring for update-on-change
    self.text_part_id.set_event_handler('pressed_enter', self._header_field_changed)
    self.text_part_id.set_event_handler('change', self._header_field_changed)
    self.text_qty.set_event_handler('pressed_enter', self._header_field_changed)
    self.text_qty.set_event_handler('change', self._header_field_changed)
    self.date_due.set_event_handler('change', self._header_field_changed)
    self.text_sales_order_id.set_event_handler('pressed_enter', self._header_field_changed)
    self.text_sales_order_id.set_event_handler('change', self._header_field_changed)
    self.drop_down_status.set_event_handler('change', self._status_changed)

    # Panels
    self.repeating_panel_route.item_template = WorkOrderRouteRow
    self.repeating_panel_materials.item_template = WorkOrderMaterialRow
    self.repeating_panel_materials.set_event_handler("x-row-changed", self._reload_materials)

    # Add component
    self.button_add_component.role = "new-button"
    self.button_add_component.set_event_handler('click', self._add_component)

    #Picklist
    self.button_generate_picklist.role = "new-button"

    #Commit stock
    self.button_commit.role = "delete-button"

    #Routing step filter
    self.drop_down_step_filter.items = ["All"]
    self.drop_down_step_filter.selected_value = "All"
    self.drop_down_step_filter.set_event_handler("change", self._on_step_filter_change)

    self._load_initial()

  # ---------- initial load ----------
  def _load_initial(self):
    self.label_wo_id.text = self.wo_id
    if self.is_new:
      self.text_part_id.text = ""
      self.text_qty.text = "1"
      self.date_due.date = None           # << correct way to clear
      self.text_sales_order_id.text = ""
      self.drop_down_status.selected_value = "planned"
  
      self.repeating_panel_route.items = []
      self.repeating_panel_materials.items = []
      self.label_materials_count.text = ""
    else:
      self._load_existing()

  def _load_existing(self):
    wo = anvil.server.call("wo_get", self.wo_id) or {}
    self._created = bool(wo)
    self.is_new = not self._created
  
    self.text_part_id.text = wo.get("part_id","")
    self.text_qty.text = str(wo.get("qty",""))
    self._wo_qty = int(wo.get("qty") or 1)
    self.date_due.date = self._to_date(wo.get("due_date"))   # << parse then set
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
    self._route_steps = sorted(
      [{"seq": int(x.get("seq", 0)), "cell_id": x.get("cell_id", "")} for x in r_items],
      key=lambda s: s["seq"]
    )
    self._seq_to_cell_id = {s["seq"]: s["cell_id"] for s in self._route_steps}
    
    # Build the step filter based on the route snapshot we just loaded
    try:
      step_seqs = [str(r.get("seq")) for r in sorted(r_items, key=lambda x: x.get("seq", 10))]
      self.drop_down_step_filter.items = ["All"] + step_seqs
      # Preserve selection if still valid; else reset to "All"
      if self.drop_down_step_filter.selected_value not in self.drop_down_step_filter.items:
        self.drop_down_step_filter.selected_value = "All"
    except Exception:
      self.drop_down_step_filter.items = ["All"]
      self.drop_down_step_filter.selected_value = "All"
    

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
  
    # For fast cell name lookup
    try:
      id_to_name = anvil.server.call("get_cell_id_to_name_map") or {}
    except Exception:
      id_to_name = {}
  
    mats = anvil.server.call("wobom_get_lines", self.wo_id) or []
  
    # Build view rows with PBOM baseline and issue step/cell tag
    view = []
    for m in mats:
      pid = m.get("part_id")
      pbom_qty = None
      if pid in self._tpl_qty_per:
        pbom_qty = self._tpl_qty_per[pid] * self._wo_qty
  
      issue_seq = m.get("issue_seq", None)
      issue_cell_id = m.get("issue_cell_id", None)
      issue_cell_name = id_to_name.get(issue_cell_id, issue_cell_id or "")
  
      view.append({
        "_doc": dict(m),
        "issue_seq": issue_seq,
        "issue_cell_name": issue_cell_name,
        "part_id": pid,
        "desc": m.get("desc",""),
        "unit": m.get("unit",""),
        "qty_required": m.get("qty_required", 0.0),
        "pbom_qty": pbom_qty,
        "is_manual": bool(m.get("is_manual", False)),
        
      })
  
    # Apply step filter
    sel = self.drop_down_step_filter.selected_value or "All"
    if sel != "All":
      try:
        sel_int = int(sel)
        view = [row for row in view if (row.get("issue_seq") == sel_int)]
      except Exception:
        pass
  
    # Sort (optional): by issue_seq, then part_id
    view.sort(key=lambda r: (r.get("issue_seq") or 10**9, str(r.get("part_id") or "")))
  
    self.repeating_panel_materials.items = view
    self.label_materials_count.text = f"{len(view)} material lines"

  def _on_step_filter_change(self, **e):
  # Just re-filter current cache by the selected step
    self._reload_materials()
  
  # ---------- header change handling ----------
  def _header_field_changed(self, **e):
    part_id = (self.text_part_id.text or "").strip()
    qty_text = (self.text_qty.text or "").strip()
    due_dt = self.date_due.date                 # << this is a date or None
    so = (self.text_sales_order_id.text or "").strip() or None
  
    # New mode: create once valid
    if not self._created:
      if not part_id or not due_dt:
        return
      try:
        qty = int(qty_text)
        if qty <= 0:
          return
      except Exception:
        return
      try:
        payload = {
          "_id": self.wo_id,
          "part_id": part_id,
          "qty": int(qty),
          "due_date": due_dt,          # << pass date object
          "sales_order_id": so,
        }
        anvil.server.call("wo_create_with_snapshots", payload)
        self._created = True
        self._load_existing()
        Notification("Work order created.", style="success").show()
      except Exception as ex:
        alert(f"Create failed: {ex}")
      return
  
    # Existing: shallow updates
    updates = {}
    try:
      q = int(qty_text)
      if q > 0 and q != self._wo_qty:
        updates["qty"] = q
    except Exception:
      pass
    if due_dt:
      updates["due_date"] = due_dt     # << date object
    updates["sales_order_id"] = so
  
    if updates:
      try:
        anvil.server.call("wo_update", self.wo_id, updates)
        if "qty" in updates:
          self._wo_qty = updates["qty"]
        Notification("Updated.", style="success").show()
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
      "anchor_part_id": (self.text_part_id.text or "").strip(),
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

  def button_add_component_click(self, **e):
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
  
    # Resolve part desc/unit (best-effort)
    try:
      pdoc = anvil.server.call("parts_get", pid) or {}
    except Exception:
      pdoc = {}
    desc = pdoc.get("description","")
    unit = pdoc.get("unit","")
  
    # Decide where to issue:
    # If a specific step is selected in the filter, use that.
    # Otherwise default to the final step (max seq) if available.
    sel = self.drop_down_step_filter.selected_value or "All"
    if sel != "All":
      try:
        issue_seq = int(sel)
      except Exception:
        issue_seq = None
    else:
      issue_seq = (self._route_steps[-1]["seq"] if self._route_steps else None)
  
    issue_cell_id = self._seq_to_cell_id.get(issue_seq) if issue_seq is not None else None
  
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
      "anchor_part_id": (self.text_part_id.text or "").strip(),
      "is_manual": True,
      # NEW: where this is consumed
      "issue_seq": issue_seq,
      "issue_cell_id": issue_cell_id,
      # optional: backflush policy; leave False for now
      "backflush": False,
    }
  
    try:
      anvil.server.call("wobom_insert_line", doc)
      self.text_add_part_id.text = ""
      self.text_add_qty.text = ""
      self._reload_materials()
      Notification("Component added.", style="success").show()
    except Exception as ex:
      alert(f"Add failed: {ex}")

  def button_generate_picklist_click(self, **event_args):
    """
    Single WO picklist grouped by destination bin.
    Opens PicklistRecord so the operator can mark picked/OOS on mobile or desktop.
    """
    try:
      pl = anvil.server.call("flow_generate_picklist_by_destination", self.wo_id) or {}
      pl_id = pl.get("_id")
      if not pl_id:
        alert("No picklist was generated (nothing to pick?)."); return
      Notification("Picklist generated.", style="success").show()
      # Navigate to the picklist UI
      try:
        from ..PicklistRecord import PicklistRecord
        open_form("PicklistRecord", picklist_id=pl_id)
      except Exception:
        # Fallback if form import path differs
        open_form("Nav")
    except Exception as ex:
      alert(f"Picklist generation failed: {ex}")
  
  def button_commit_click(self, **event_args):
    """
    Batch commit: consume all reservations on this WO (journal issues).
    """
    try:
      summary = anvil.server.call("wo_commit_all_picks", self.wo_id) or {}
      msg = f"Committed: {int(summary.get('consumed',0))} lines; Skipped: {int(summary.get('skipped',0))}"
      Notification(msg, style="success").show()
      self._reload_materials()
    except Exception as ex:
      alert(f"Commit failed: {ex}")

  
  def _to_date(self, v):
    """Accepts None | date | str('YYYY-MM-DD') and returns date|None."""
    if v is None or v == "":
      return None
    if isinstance(v, date):
      return v
    s = str(v).strip()
    try:
      return date.fromisoformat(s)
    except Exception:
      try:
        # last-ditch: parse 'YYYY-MM-DD...' (if there's a time portion)
        return datetime.fromisoformat(s).date()
      except Exception:
        return None
