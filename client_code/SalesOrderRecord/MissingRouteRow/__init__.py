# MissingRouteRow — explicit render, no data bindings

from anvil import *
from ._anvil_designer import MissingRouteRowTemplate
import anvil.server

class MissingRouteRow(MissingRouteRowTemplate):
  def __init__(self, **kwargs):
    self.init_components(**kwargs)
    for w in [getattr(self, "label_part_id", None),
              getattr(self, "label_reason", None),
              getattr(self, "button_open_part", None),
              getattr(self, "button_open_ops", None)]:
      if w and hasattr(w, "data_bindings"):
        try:
          w.data_bindings = []
        except Exception:
          pass
    self.set_item(self.item or kwargs.get("item") or {})

  def set_item(self, item):
    i = dict(item or {})
    if hasattr(self, "label_part_id"):
      self.label_part_id.text = i.get("part_id") or ""
    if hasattr(self, "label_reason"):
      self.label_reason.text = i.get("reason") or "no route"

  def button_open_part_click(self, **e):
    pid = (self.item or {}).get("part_id")
    if pid:
      try:
        anvil.server.call("svc_ui_open_part_record", pid)
      except Exception as ex:
        alert(f"Open Part failed: {ex}")

  def button_open_ops_click(self, **e):
    pid = (self.item or {}).get("part_id")
    if pid:
      try:
        anvil.server.call("svc_ui_open_part_route_ops", pid)
      except Exception as ex:
        alert(f"Open PartRouteOps failed: {ex}")

