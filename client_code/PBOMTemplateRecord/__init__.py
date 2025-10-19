
from anvil import *
import anvil.server
import re
from ._anvil_designer import PBOMTemplateRecordTemplate

class PBOMTemplateRecord(PBOMTemplateRecordTemplate):
  """
  Header:
    - parent_id: TextBox        (text_parent_id)
    - status:    DropDown       (drop_down_status)
    - rev:       DropDown       (drop_down_rev)
    - plant:     TextBox        (text_plant)
    - variant:   TextBox        (text_variant)
    - notes:     TextArea       (text_notes)

  Behaviour:
    - New (pbom_id is None): enter parent_id, press Enter to resolve; choose initial rev; click Save to create.
    - Existing: header auto-saves on change while status == 'draft'; Save button performs an explicit update of header fields.
    - Rev changes:
        * New: choosing a value just sets the initial rev for creation.
        * Existing: selecting "next" rev clones a new PBOM via pbomtpl_revise_from and opens it in-place.
    - Status changes follow draft→active→obsolete→archived transitions.
  """

  def __init__(self, pbom_id=None, parent_prefix="", status="", rev="", plant="", **kwargs):
    self.init_components(**kwargs)
    self.pbom_id = pbom_id if pbom_id else None
    self.doc = {}
    self._status = "draft"   # cached status
    self._rev = ""           # cached rev

    # Roles
    self.repeating_panel_lines.role = "scrolling-panel"
    self.button_home.role = "mydefault-button"
    self.button_regenerate.role = "new-button"
    self.button_save.role = "save-button"

    # Events
    self.text_parent_id.set_event_handler("pressed_enter", self._resolve_parent_on_enter)
    self.text_plant.set_event_handler("change", self.text_plant_change)
    self.text_variant.set_event_handler("change", self.text_variant_change)
    self.text_notes.set_event_handler("change", self.text_notes_change)
    self.drop_down_status.set_event_handler("change", self.drop_down_status_change)
    self.drop_down_rev.set_event_handler("change", self.drop_down_rev_change)
    self.button_save.set_event_handler("click", self.button_save_click)

    if self.pbom_id:
      self._load()
    else:
      self._init_new_blank(parent_prefix, status, rev, plant)

  # ---------- New-record (unsaved) mode ----------

  def _init_new_blank(self, parent_prefix, status, rev, plant):
    self.label_id.text = "(unsaved)"
    self.text_parent_id.text = ""
    self.label_parent_desc.text = ""
    self.text_plant.text = (plant or "").strip()
    self.text_variant.text = ""
    self.text_notes.text = ""
    self.repeating_panel_lines.items = []

    # Save & regenerate buttons
    self.button_save.visible = True
    self.button_save.enabled = False           # enabled after valid parent resolve
    self.button_regenerate.visible = False     # cannot regenerate until created

    # Status dropdown: force 'draft', disabled until created
    self._status = "draft"
    self._bind_status_dropdown(self._status)
    self.drop_down_status.enabled = False

    # Rev dropdown for new record: allow choosing initial revision
    self._rev = (rev or "").strip() or "A"
    self._bind_rev_dropdown(self._rev, is_archived=False)
    self.drop_down_rev.enabled = True

    # Enable header entry fields
    for c in [self.text_parent_id, self.text_plant, self.text_variant, self.text_notes]:
      c.enabled = True

  def _resolve_parent_on_enter(self, **e):
    pid = (self.text_parent_id.text or "").strip()
    if not pid:
      Notification("Enter a valid parent_id.").show()
      return
    try:
      part = anvil.server.call("get_part_brief", pid)
    except Exception as ex:
      alert(f"Lookup failed: {ex}")
      return

    if not part:
      self.label_parent_desc.text = ""
      self.button_save.enabled = False
      Notification("Parent not found.").show()
      return

    self.label_parent_desc.text = part.get("description") or part.get("part_name") or ""
    self.button_save.enabled = True

  # ---------- Existing-record mode ----------

  def _load(self):
    d = anvil.server.call("pbomtpl_get", self.pbom_id) or {}
    self._bind_header_from_doc(d)
    self.repeating_panel_lines.items = (d.get("lines") or [])

  # ---------- Header binding & autosave ----------

  def _bind_header_from_doc(self, d):
    # Cache first
    self.doc = d or {}
    self._status = (self.doc.get("status") or "draft")
    self._rev    = (self.doc.get("rev") or "")

    # Header controls
    self.label_id.text          = (self.doc.get("_id") or "") or ""
    self.text_parent_id.text    = (self.doc.get("parent_part_id") or "") or ""
    self.label_parent_desc.text = (self.doc.get("parent_desc") or "") or ""
    self.text_plant.text        = (self.doc.get("plant_id") or "") or ""
    self.text_variant.text      = (self.doc.get("variant") or "") or ""
    self.text_notes.text        = (self.doc.get("notes") or "") or ""

    # Enable/disable header fields by status
    is_draft = (self._status == "draft")
    for c in [self.text_parent_id, self.text_plant, self.text_variant, self.text_notes]:
      c.enabled = is_draft

    # Status & Rev dropdowns
    self._bind_status_dropdown(self._status)
    self._bind_rev_dropdown(self._rev, is_archived=(self._status == "archived"))

    # Buttons
    self.button_save.visible = True
    self.button_save.enabled = True if is_draft else False
    self.button_regenerate.visible = True
    self.button_regenerate.enabled = is_draft

  def _save_header(self, patch):
    if not patch or not self.pbom_id:
      return
    if self._status != "draft":
      Notification("Header is read-only (status ≠ draft).").show()
      return
    try:
      updated = anvil.server.call("pbomtpl_update", self.pbom_id, patch) or {}
      self._bind_header_from_doc(updated)
    except Exception as e:
      alert(f"Save failed: {e}")

  def text_parent_id_change(self, **e):
    # Only allowed for existing drafts; in new mode, parent resolves via Enter before Save
    if not self.pbom_id:
      return
    pid = (self.text_parent_id.text or "").strip()
    try:
      part = anvil.server.call("get_part_brief", pid) if pid else None
      self.label_parent_desc.text = (part or {}).get("description") or (part or {}).get("part_name") or ""
    except Exception:
      self.label_parent_desc.text = ""
    self._save_header({"parent_part_id": pid})

  def text_plant_change(self, **e):
    self._save_header({"plant_id": (self.text_plant.text or None) or None})

  def text_variant_change(self, **e):
    self._save_header({"variant": (self.text_variant.text or None) or None})

  def text_notes_change(self, **e):
    self._save_header({"notes": (self.text_notes.text or None) or None})

  # ---------- Status & Revision ----------

  def _bind_status_dropdown(self, current):
    # draft -> active -> obsolete -> archived
    allowed_map = {
      "draft":    ["draft", "active"],
      "active":   ["active", "obsolete"],
      "obsolete": ["obsolete", "archived"],
      "archived": ["archived"],
    }
    items = allowed_map.get(current, [current])
    self.drop_down_status.items = items
    self.drop_down_status.selected_value = current
    # Enabled only if next state exists and doc exists
    self.drop_down_status.enabled = (len(items) > 1) and bool(self.pbom_id)

  def drop_down_status_change(self, **e):
    if not self.pbom_id:
      # Cannot change status before the record exists
      self._bind_status_dropdown("draft")
      return

    old = self._status
    new = self.drop_down_status.selected_value or old
    if new == old:
      return
    try:
      updated = anvil.server.call("pbomtpl_set_status", self.pbom_id, new)
      if not updated:
        Notification("Transition not permitted").show()
        self.drop_down_status.selected_value = old
        return
      self._bind_header_from_doc(updated)
    except Exception as ex:
      alert(f"Failed to change status: {ex}")
      self.drop_down_status.selected_value = old

  def _bind_rev_dropdown(self, current_rev, is_archived):
    # [current_rev, next_rev]; if none, offer ["A"]
    next_rev = self._next_alpha_rev(current_rev or "")
    items = []
    if current_rev:
      items.append(current_rev)
    if next_rev and next_rev != current_rev:
      items.append(next_rev)
    if not items:
      items = ["A"]

    self.drop_down_rev.items = items
    self.drop_down_rev.selected_value = current_rev if current_rev in items else items[0]
    # Enabled in two cases:
    #  - existing, not archived, next exists
    #  - new (pbom_id is None), to choose initial rev
    self.drop_down_rev.enabled = (not is_archived and len(items) > 1 and bool(self.pbom_id)) or (not self.pbom_id)

  def drop_down_rev_change(self, **e):
    # New: just set intended initial rev
    if not self.pbom_id:
      self._rev = self.drop_down_rev.selected_value or "A"
      return

    # Existing: clone to next rev
    current_rev = self.doc.get("rev") or ""
    selected_rev = self.drop_down_rev.selected_value or current_rev
    if selected_rev == current_rev:
      return
    try:
      clone = anvil.server.call("pbomtpl_revise_from", self.pbom_id, selected_rev)
      if clone:
        # In-place open of the cloned record
        self.pbom_id = clone.get("_id")
        self._bind_header_from_doc(clone)
        self.repeating_panel_lines.items = (clone.get("lines") or [])
    except Exception as ex:
      alert(f"Failed to create revision: {ex}")
      self.drop_down_rev.selected_value = current_rev

  def _next_alpha_rev(self, cur):
    if not cur:
      return "A"
    if re.fullmatch(r"[A-Z]+", cur):
      chars = list(cur)
      i = len(chars) - 1
      carry = True
      while i >= 0 and carry:
        if chars[i] == 'Z':
          chars[i] = 'A'
          i -= 1
        else:
          chars[i] = chr(ord(chars[i]) + 1)
          carry = False
      return ("A" + "".join(chars)) if carry else "".join(chars)
    m = re.fullmatch(r"(.*?)(\d+)$", cur)
    if m:
      head, digits = m.groups()
      return f"{head}{int(digits)+1:0{len(digits)}d}"
    return cur + "A"

  # ---------- Save (create OR update) ----------
  def button_save_click(self, **e):
    """
    - If pbom_id is None: validate parent, create draft via pbomtpl_create_draft, bind in-place.
    - Else (existing): push current editable header fields via pbomtpl_update (draft only).
    """
    pid = (self.text_parent_id.text or "").strip()

    if not self.pbom_id:
      # CREATE
      if not pid:
        Notification("Enter a valid parent_id first.").show()
        return
      payload = {
        "parent_part_id": pid,
        "rev": (self.drop_down_rev.selected_value or "A"),
        "plant_id": (self.text_plant.text or None) or None,
        "variant": (self.text_variant.text or None) or None,
        "notes": (self.text_notes.text or None) or None,
      }
      try:
        created = anvil.server.call("pbomtpl_create_draft", payload) or {}
      except Exception as ex:
        alert(f"Save failed: {ex}")
        return

      created_id = created.get("_id") or created.get("id") or created.get("pbom_id")
      if not created_id:
        alert(f"Create succeeded but no _id was returned.\nReturned: {created!r}")
        return

      # In-place transition to existing
      self.pbom_id = created_id
      self._bind_header_from_doc(created)
      self.repeating_panel_lines.items = (created.get("lines") or [])
      Notification("Production BOM created.").show()
      return

    # UPDATE (existing)
    if self._status != "draft":
      Notification("This Production BOM is not editable (status ≠ draft).").show()
      return

    patch = {
      "parent_part_id": pid or None,
      "plant_id": (self.text_plant.text or None) or None,
      "variant": (self.text_variant.text or None) or None,
      "notes": (self.text_notes.text or None) or None,
    }
    # Remove keys that are None to avoid unintentional nulling (optional)
    patch = {k: v for k, v in patch.items() if v is not None or k == "parent_part_id"}

    try:
      updated = anvil.server.call("pbomtpl_update", self.pbom_id, patch) or {}
      self._bind_header_from_doc(updated)
      Notification("Saved.").show()
    except Exception as ex:
      alert(f"Save failed: {ex}")

  # ---------- Lines ----------
  def button_regenerate_click(self, **e):
    if self._status != "draft":
      Notification("Can only regenerate lines while in draft.").show()
      return
    if confirm("Rebuild lines from DesignBOM? This will replace current lines."):
      try:
        d = anvil.server.call("pbomtpl_regenerate_from_design", self.pbom_id) or {}
      except Exception as ex:
        alert(f"Regenerate failed: {ex}")
        return
      # Reload/bind after regenerate
      self._bind_header_from_doc(d or self.doc)
      self.repeating_panel_lines.items = (d.get("lines") if d else self.doc.get("lines") or [])

  # ---------- Navigation ----------
  def button_home_click(self, **event_args):
    open_form("Nav")

