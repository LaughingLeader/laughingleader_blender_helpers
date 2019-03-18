bl_info = {
    "name": "LaughingLeader Helpers",
    "author": "LaughingLeader",
    "blender": (2, 7, 9),
    "api": 38691,
    "location": "",
    "description": (""),
    "warning": "",
    "wiki_url": (""),
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "System"}

import bpy

from bpy.types import (
        Operator,
        Panel,
        UIList,
        PropertyGroup,
        AddonPreferences,
        )
from bpy.props import (
        StringProperty,
        BoolProperty,
        IntProperty,
        CollectionProperty,
        BoolVectorProperty,
        PointerProperty,
        )

# load and reload submodules
##################################

import importlib
from . import developer_utils
importlib.reload(developer_utils)
modules = developer_utils.setup_addon_modules(__path__, __name__, "bpy" in locals())

class LeaderAddonPreferencesData(bpy.types.PropertyGroup):
    bl_idname = ""

    label = StringProperty()
    props = []

    def draw(self, context):
        col = self.layout.col()
        col.label(text=self.label)
        return

class LeaderPreferencesList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            item.draw(context, layout)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class LeaderHelpersAddonPreferences(AddonPreferences):
    bl_idname = __name__

    addon_preferences_list = []

    #def layer_manager_categyory_updated(self, context):

    from . import layer_manager

    layer_manager_enabled = BoolProperty(default=True, name="Enable Layer Manager", update=layer_manager.enabled_changed)
    layer_manager_category = StringProperty(default="Layers", name="Layer Manager Panel Name", update=layer_manager.update_panel)

    def draw(self, context):
        #self.layout.template_list("LeaderPreferencesList", "", self, "preference_data", self, "index")

        # for drawable in LeaderHelpersAddonPreferences.addon_preferences_list:
        #     drawfunc = getattr(drawable, "draw", None)
        #     if callable(drawfunc):
        #         #drawfunc(drawable, context, self.layout)
        #         self.layout.prop
        layout = self.layout
        layout.prop(self, "layer_manager_enabled")
        layout.prop(self, "layer_manager_category")
        return
# register
##################################

import traceback

def register():
    try: bpy.utils.register_module(__name__)
    except: traceback.print_exc()

    print("Registered {} with {} modules".format(bl_info["name"], len(modules)))
    
    for module in modules:
        register_func = getattr(module, "register", None)
        if callable(register_func):
            register_func()

def unregister():
    for module in modules:
        unregister_func = getattr(module, "unregister", None)
        if callable(unregister_func):
            unregister_func()
    
    try: bpy.utils.unregister_module(__name__)
    except: traceback.print_exc()

    print("Unregistered {}".format(bl_info["name"]))

#print("__init__.py running? {}".format(__name__))

if __name__ == "__main__":
    register()