from ._anvil_designer import SidebarMenuItemTemplate
from anvil import *
import anvil.server


class SidebarMenuItem(SidebarMenuItemTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.nav_button.role = "sidebar-button"

  def form_show(self, **event_args):
    self.nav_button.text = self.item['title']

  def nav_button_click(self, **event_args):
    self.parent.raise_event('x-load-form', 
                            title=self.item['title'], 
                            form_class=self.item['form_class'])

