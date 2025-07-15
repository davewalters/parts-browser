from ._anvil_designer import SidebarMenuItemTemplate
from anvil import *
import anvil.server


class SidebarMenuItem(SidebarMenuItemTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
    self.nav_button.role = "mydefault-button"

  def form_show(self, **event_args):
    print("SidebarMenuItem.item:", self.item)
    print ("form_show_called")
    #self.nav_button.text = self.item['title']
    self.nav_button.text = "TEST BUTTON"

  def nav_button_click(self, **event_args):
    self.parent.raise_event('x-load-form', 
                            title=self.item['title'], 
                            form_class=self.item['form_class'])

