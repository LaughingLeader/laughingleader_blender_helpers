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
        EnumProperty,
        FloatProperty
        )

import bpy_extras.keyconfig_utils
import traceback
from bpy.app.handlers import persistent

import os.path
import os

# load and reload submodules
##################################

import importlib
from . import developer_utils
importlib.reload(developer_utils)
modules = developer_utils.setup_addon_modules(__path__, __name__, "bpy" in locals())

class LeaderAddonPreferencesData(bpy.types.PropertyGroup):
    bl_idname = "leader_addonpreferencesdata"

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
    bl_idname = "laughingleader_blender_helpers"

    addon_preferences_list = []

    general_enable_deletion = BoolProperty(
        name="Enable Delete Buttons",
        description="Enable visibility of delete buttons for data (actions, textures, etc)",
        default=False
    )

    debug_mode = BoolProperty(
        name="Enable Debug Mode",
        description="Auto-opens the console window on load, and enables other debug features",
        default=False
    )

    from . import layer_manager

    layer_manager_enabled = BoolProperty(default=True, name="Enable", description="Enable the Layer Manager", update=layer_manager.enabled_changed)
    #layer_manager_default_showextras = BoolProperty(default=False, name="Show Extras by Default", description="Show the extra options for layers by default. This can be overwritten in the Layer Manager panel")
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

    uvhelpers_errorchecker_length_check_value = IntProperty(
        name="Precision",
        description="The minimum length for UV triangles. Lengths less than this value will be selected as an error.\nThe final precision value is x/100000000",
        default=10,
        min=1
    )

    uvhelpers_images_quickexport_filepath = StringProperty(
        name="Export Filepath",
        description="The file path to export the image to",
        default=""
    )

    uvhelpers_images_quickexport_last_filepath = StringProperty(
        options={"HIDDEN"},
        default=""
    )

    uvhelpers_images_quickexport_filename_ext = StringProperty(
        name="File Extension",
        options={"HIDDEN"},
        default=".png"
    )

    uvhelpers_images_quickexport_directory = StringProperty(
        name="Directory",
        default="",
        options={"HIDDEN"}
    )

    def images_quickexport_update_filepath(self, context):
        fp = self.uvhelpers_images_quickexport_filepath
        fp_last = self.uvhelpers_images_quickexport_last_filepath
        fp_dir = self.uvhelpers_images_quickexport_directory
        fp_auto = self.uvhelpers_images_quickexport_autoname
        fp_manual = self.uvhelpers_images_quickexport_manualname
        fp_append = self.uvhelpers_images_quickexport_append
        ext = self.uvhelpers_images_quickexport_filename_ext
        fp_result = ""

        if fp != "" and fp_last == "":
            self.uvhelpers_images_quickexport_last_filepath = fp

        if fp_dir == "":
            fp_dir = os.path.dirname(bpy.data.filepath)

        if fp == "":
            fp = "{}\\{}".format(fp_dir, str.replace(bpy.path.basename(bpy.data.filepath), ".blend", ""))

        if fp != "":
            if fp_manual != "":
                fp = "{}\\{}".format(fp_dir, fp_manual)
            else:
                if fp_auto == "LAYER":
                    if hasattr(bpy.data.scenes["Scene"], "namedlayers"):
                        for i in range(20):
                            if (bpy.data.scenes["Scene"].layers[i]):
                                    layername = bpy.data.scenes["Scene"].namedlayers.layers[i].name
                                    if layername is not None and layername != "":
                                        fp = "{}\\{}".format(fp_dir, layername)
                                        break
                elif fp_auto == "OBJECT":
                    obj_name = "object"
                    if getattr(context.scene.objects, "active", None) is not None and hasattr(context.scene.objects.active, "name"):
                        obj_name = context.scene.objects.active.name
                    fp = "{}\\{}".format(fp_dir, obj_name)
                    print("Obj name: {}".format(obj_name))
                elif fp_auto == "DISABLED" and fp_last != "":
                    fp = fp_last
        fp = "{}_{}".format(fp, fp_append)
        fp_result = bpy.path.ensure_ext(fp, ext)
        print("Test: {} | {}".format(fp_dir, fp))
        self.uvhelpers_images_quickexport_directory = fp_dir
        self.uvhelpers_images_quickexport_filepath = fp_result
        return

    uvhelpers_images_quickexport_autoname = EnumProperty(
        name="Auto-Name",
        description="Auto-generate a filename based on a property name",
        items=(("DISABLED", "Disabled", ""),
               ("LAYER", "Layer Name", ""),
               ("OBJECT", "Active Object Name", "")),
        default=("LAYER"),
        update=images_quickexport_update_filepath
    )

    uvhelpers_images_quickexport_manualname = StringProperty(
        name="Manual Name",
        description="The name to use when quick exporting (leave blank to disable)",
        default="",
        update=images_quickexport_update_filepath
    )

    uvhelpers_images_quickexport_append = StringProperty(
        name="Append",
        description="Append the text at the end of the file name",
        default="",
        update=images_quickexport_update_filepath
    )

    def draw(self, context):
        #self.layout.template_list("LeaderPreferencesList", "", self, "preference_data", self, "index")

        # for drawable in LeaderHelpersAddonPreferences.addon_preferences_list:
        #     drawfunc = getattr(drawable, "draw", None)
        #     if callable(drawfunc):
        #         #drawfunc(drawable, context, self.layout)
        #         self.layout.prop
        layout = self.layout
        layout.label("General")
        box = layout.box()
        box.prop(self, "general_enable_deletion")
        layout.label("Layer Manager")
        box = layout.box()
        box.prop(self, "layer_manager_enabled")
        box.prop(self, "layer_manager_category")
        #box.prop(self, "layer_manager_default_showextras")
        layout.prop(self, "viewport_shading_target")
        layout.prop(self, "debug_mode")
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
            preferences = context.user_preferences.addons["laughingleader_blender_helpers"].preferences
            if preferences is not None:
                target = preferences.viewport_shading_target
                last = preferences.viewport_shading_last
                #Source: https://blender.stackexchange.com/a/17746
                area = next(area for area in bpy.context.screen.areas if area.type == "VIEW_3D")
                space = next(space for space in area.spaces if space.type == "VIEW_3D")

                if space.viewport_shade != target:
                    preferences.viewport_shading_last = space.viewport_shade
                    space.viewport_shade = target
                else:
                    space.viewport_shade = last
        except Exception as e:
            print("[LeaderHelpers] Error setting viewport shading:\n{}".format(e))
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
    try:
        for km, kmi in addon_keymaps:
            print("[LeaderHelpers] Removed keybinding '{}'('{}').".format(kmi.idname, kmi.name))
            km.keymap_items.remove(kmi)
        #wm.keyconfigs.default.keymaps.remove(km)
    except: pass
    addon_keymaps.clear()
    print("[LeaderHelpers] Unregistered keybindings.")

toggled_console = False

@persistent
def load_post_init(scene):
    global toggled_console
    if toggled_console == False:
        try:
            preferences = bpy.context.user_preferences.addons["laughingleader_blender_helpers"].preferences
            if preferences is not None:
                if preferences.debug_mode == True:
                    print("[LeaderHelpers] Debug mode is enabled. Toggling system console window.")
                    bpy.ops.wm.console_toggle()
        except: pass
        toggled_console = True
        bpy.app.handlers.load_post.remove(load_post_init)

def register():
    try: bpy.utils.register_module(__name__)
    except: traceback.print_exc()

    print("[LeaderHelpers] Registered {} with {} modules".format(bl_info["name"], len(modules)))
    
    for module in modules:
        register_func = getattr(module, "register", None)
        if callable(register_func):
            #print("[LeaderHelpers] Calling register() for {} ".format(module))
            register_func()

    register_keymaps()

    bpy.app.handlers.load_post.append(load_post_init)

    #wm = bpy.context.window_manager
    #bpy_extras.keyconfig_utils.keyconfig_test(wm.keyconfigs.default)

def unregister():
    for module in modules:
        unregister_func = getattr(module, "unregister", None)
        if callable(unregister_func):
            unregister_func()

    try: 
        bpy.utils.unregister_module(__name__)
        bpy.app.handlers.load_post.remove(load_post_init)
    except: traceback.print_exc()

    unregister_keymaps()
    print("Unregistered {}".format(bl_info["name"]))

#print("__init__.py running? {}".format(__name__))

if __name__ == "__main__":
    register()