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
        EnumProperty
        )

import bpy_extras.keyconfig_utils

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
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            item.draw(context, layout)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)

shading_modes = (
        ("BOUNDBOX", "Bounding Box", "Display the object’s local bounding boxes only"),
        ("WIREFRAME", "Wireframe", "Display the object as wire edges"),
        ("SOLID", "Solid", " Display the object solid, lit with default OpenGL lights"),
        ("TEXTURED", "Textured", "Display the object solid, with a texture"),
        ("MATERIAL", "Material", "Display objects solid, with GLSL material"),
        ("RENDERED", "Rendered", "Display render preview")
)

select_modes = (
        ("FACE", "Face", ""),
        ("EDGE", "Edge", ""),
        ("VERTEX", "Vertex", "")
)

class LeaderHelpersAddonPreferences(AddonPreferences):
    bl_idname = __name__

    addon_preferences_list = []

    #def layer_manager_categyory_updated(self, context):

    from . import layer_manager

    layer_manager_enabled = BoolProperty(default=True, name="Enable", description="Enable the Layer Manager", update=layer_manager.enabled_changed)
    layer_manager_category = StringProperty(default="Layers", name="Panel Name", description="Display name to use for the Layer Manager Panel", update=layer_manager.update_panel)

    viewport_shading_target = EnumProperty(
        name="Toggle Viewport Shading Target",
        description="The shading type to switch to when toggling the viewport shading",
        items=shading_modes,
        default=("MATERIAL")
    )

    viewport_shading_last = EnumProperty(default=("SOLID"), items=shading_modes, options={"HIDDEN"})

    uvhelpers_errorchecker_select_all = BoolProperty(
            name="Select All Problems",
            description="Select all problematic UVs. If disabled, will only select the first problem found",
            default=False
    )

    uvhelpers_errorchecker_select_mode = EnumProperty(
        name="Mode",
        description="The selection mode to use when selecting bad UVs",
        items=select_modes,
        default=("VERTEX")
    )

    def draw(self, context):
        #self.layout.template_list("LeaderPreferencesList", "", self, "preference_data", self, "index")

        # for drawable in LeaderHelpersAddonPreferences.addon_preferences_list:
        #     drawfunc = getattr(drawable, "draw", None)
        #     if callable(drawfunc):
        #         #drawfunc(drawable, context, self.layout)
        #         self.layout.prop
        layout = self.layout
        box = layout.box()
        box.label(text="Layer Manager")
        box.prop(self, "layer_manager_enabled")
        box.prop(self, "layer_manager_category")
        layout.prop(self, "viewport_shading_target")
        return

class LeaderToggleViewportShading(Operator):
    """Print the list of active addons to the debug window"""
    bl_idname = "llhelpers.op_toggle_viewport_shading"
    bl_label = "Toggle Viewport Shading (Leader Helpers)"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {"FINISHED"}
    
    def invoke(self, context, event):
        try:
            target = context.user_preferences.addons[LeaderHelpersAddonPreferences.bl_idname].preferences.viewport_shading_target
            last = context.user_preferences.addons[LeaderHelpersAddonPreferences.bl_idname].preferences.viewport_shading_last
            #Source: https://blender.stackexchange.com/a/17746
            area = next(area for area in bpy.context.screen.areas if area.type == "VIEW_3D")
            space = next(space for space in area.spaces if space.type == "VIEW_3D")

            if space.viewport_shade != target:
                context.user_preferences.addons[LeaderHelpersAddonPreferences.bl_idname].preferences.viewport_shading_last = space.viewport_shade
                space.viewport_shade = target
            else:
                space.viewport_shade = last
        except Exception as e:
            print("Error setting viewport shading:\n{}".format(e))
            pass
        return {"FINISHED"}

# register
##################################

addon_keymaps = []
#leader_keymap_category = ('Leader Helpers', 'EMPTY', 'WINDOW', [])

def register_keymaps():
    # This bit makes Leader Helpers visible in the UI
    # if not leader_keymap_category in bpy_extras.keyconfig_utils.KM_HIERARCHY:
    #     bpy_extras.keyconfig_utils.KM_HIERARCHY.append(leader_keymap_category)
    #     bpy_extras.keyconfig_utils.KM_HIERARCHY.sort() # optional

    wm = bpy.context.window_manager

    km = wm.keyconfigs.default.keymaps.new('3D View', space_type='VIEW_3D', region_type='WINDOW', modal=False)

    kmi = km.keymap_items.new(LeaderToggleViewportShading.bl_idname, type='NONE', value='PRESS')
    addon_keymaps.append((km, kmi))

    print("[LeaderHelpers] Registered keybindings.")

def unregister_keymaps():
    # bpy_extras.keyconfig_utils.KM_HIERARCHY.remove(leader_keymap_category)
    # for entry in bpy_extras.keyconfig_utils.KM_HIERARCHY:
    #     idname, spaceid, regionid, children = entry
    #     if idname == 'Leader Helpers':
    #         bpy_extras.keyconfig_utils.KM_HIERARCHY.remove(entry)
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.default
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    print("[LeaderHelpers] Unregistered keybindings.")

import traceback

def register():
    try: bpy.utils.register_module(__name__)
    except: traceback.print_exc()

    print("Registered {} with {} modules".format(bl_info["name"], len(modules)))
    
    for module in modules:
        register_func = getattr(module, "register", None)
        if callable(register_func):
            print("Calling register() for {} ".format(module))
            register_func()

    register_keymaps()

    #wm = bpy.context.window_manager
    #bpy_extras.keyconfig_utils.keyconfig_test(wm.keyconfigs.default)

def unregister():
    unregister_keymaps()
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