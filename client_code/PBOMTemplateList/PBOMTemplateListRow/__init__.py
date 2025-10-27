from ._anvil_designer import PBOMTemplateListRowTemplate
from anvil import *
import anvil.server

class PBOMTemplateListRow(PBOMTemplateListRowTemplate):
  def __init__(self, **kwargs):
    # IMPORTANT: __init__ receives 'item' via **kwargs from the RepeatingPanel.
    self.init_components(**kwargs)

    # Remove any designer bindings that might conflict
    for w in [
      self.label_id,
      self.label_parent_id,
      self.label_parent_desc,
      self.label_rev,
      self.label_plant,
      self.label_variant,
      self.label_status,
    ]:
      try:
        w.data_bindings = []
      except Exception:
        pass

    # Render immediately from the initial item (mirrors your CustomerRecordsRow pattern)
    self._render(self.item or kwargs.get("item") or {})

  # RepeatingPanel calls this whenever it (re)assigns the row's item
  def set_item(self, item):
    self.item = item or {}
    self._render(self.item)

  def _render(self, i):
    self.label_id.text          = (i.get("display_id") or i.get("id") or i.get("_id") or "")
    self.label_parent_id.text   = i.get("parent_part_id") or ""
    self.label_parent_desc.text = i.get("parent_desc") or ""
    self.label_rev.text         = i.get("rev") or ""
    self.label_plant.text       = i.get("plant_id") or ""
    self.label_variant.text     = i.get("variant") or ""
    self.label_status.text      = i.get("status") or ""

  def _ancestor_rp(self):
    # Row template may be wrapped by a DataRowPanel inside the RP
    p = getattr(self, "parent", None)
    if p and hasattr(p, "items"):         # row's parent IS the RP
      return p
    if p and getattr(p, "parent", None) and hasattr(p.parent, "items"):
      return p.parent                      # row's parent is DRP; its parent is the RP
    return None
 
  def button_select_click(self, **event_args):
    i = self.item or {}
    db_id = i.get("_id")
    if not db_id:
      Notification("Missing PBOM _id on row.").show()
      return
    open_form("PBOMTemplateRecord",
              pbom_id=db_id,
              parent_prefix="",
              status="",
              rev="",
              plant="")

  def button_delete_click(self, **event_args):
    i = self.item or {}
    db_id = i.get("_id") or i.get("id")
    disp  = i.get("display_id") or db_id or ""
    if not db_id:
      Notification("Missing PBOM _id on row.", style="warning").show()
      return
    if not confirm(f"Delete PBOM {disp}? This cannot be undone."):
      return

    try:
      res = anvil.server.call("pbomtpl_delete", db_id) or {}
    except Exception as e:
      alert(f"Delete failed: {e}")
      return

    if res.get("deleted_count", 0) != 1:
      Notification("Delete failed or not found.", style="warning").show()
      return

    Notification("PBOM deleted.", style="danger").show()

    # Prefer immediate in-place removal from the RP items (fast, no requery)
    rp = self._ancestor_rp()
    if rp:
      cur = list(rp.items or [])
      # remove by matching any of the known ids
      def _same(x):
        return (x.get("_id") == db_id) or (x.get("id") == db_id) or (x.get("display_id") == disp)
      new_items = [x for x in cur if not _same(x)]
      rp.items = new_items
      # also try to let the list update its count label (if it listens)
      try:
        rp.raise_event("x-items-changed", count=len(new_items))
      except Exception:
        pass
    else:
      # Fallback: ask the parent list form to reload
      try:
        self.raise_event("x-refresh-list")
      except Exception:
        pass





