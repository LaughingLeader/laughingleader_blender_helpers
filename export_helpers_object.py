from __future__ import division
import bpy
from bpy.types import Operator, AddonPreferences, PropertyGroup, UIList, Panel
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty

import addon_utils

bl_info = {
    "name": "Export Helpers",
    "author": "LaughingLeader",
    "blender": (2, 7, 9),
    "api": -1,
    "location": "Properties > Export Settings",
    "description": ("Helpers for customizing file export"),
    "warning": "",
    "wiki_url": (""),
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "Properties"
}

class AddonDebugOperator(Operator):
    """Print the list of active addons to the debug window"""
    bl_idname = "llhelpers.export_addondebug"
    bl_label = "List Active Addons (Debug)"

    def execute(self, context):        # execute() is called when running the operator.
        import sys
        paths_list = addon_utils.paths()
        addon_list = []
        for path in paths_list:
            bpy.utils._sys_path_ensure(path)
            for mod_name, mod_path in bpy.path.module_names(path):
                is_enabled, is_loaded = addon_utils.check(mod_name)
                addon_list.append(mod_name)
                print("%s default:%s loaded:%s"%(mod_name,is_enabled,is_loaded))
        
        return {'FINISHED'}

class LLObjectExportProperties(PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Object.llexportprops = PointerProperty(
            name="Export Properties",
            description="Various export options",
            type=cls,
            )

        def export_name_changed(self, context):
            self.original_name = context.object.name
            if self.export_name == "__DEFAULT__":
                self.export_name = self.original_name

        cls.export_name = StringProperty(
            name="Export Name",
            description="The name to use for the object when exporting",
            default="__DEFAULT__", # Little workaround so "Reset to Default Value" uses the object name
            update=export_name_changed
        )

        cls.original_name = StringProperty(
            options={"HIDDEN"},
            default=""
        )

        cls.apply_transforms = EnumProperty(
            name="Apply Transformations",
            description="Apply transformations when exporting",
            items=(("DISABLED", "Disabled", ""),
                ("SCALE", "Scale", ""),
                ("ROT", "Rotation", ""),
                ("LOC", "Location", ""),
                ("ROTSCALE", "Rotation/Scale", ""),
                ("LOCSCALE", "Location/Scale", ""),
                ("LOCROT", "Location/Rotation", ""),
                ("ALL", "Location/Rotation/Scale", "")),
            default=("DISABLED")
            )

        cls.initialized = BoolProperty(
            options={"HIDDEN"},
            default=False
        )

    def draw(self, layout, context, obj):
        layout.prop(self, "export_name")
        layout.prop(self, "apply_transforms")

    def prepare(self, context, obj):
        transform_option = obj.llexportprops.apply_transforms
        if self.apply_transforms != "DISABLED":
            last_selected = getattr(bpy.context.scene.objects, "active", None)
            bpy.context.scene.objects.active = obj
            obj.select = True
            bpy.ops.object.mode_set(mode="OBJECT")
            print("[LLHelpers-Export] Applying transformations for {} ({})".format(obj.name, transform_option))
            if transform_option == "ALL":
                bpy.ops.object.transform_apply(location = True, rotation = True, scale = True)
            elif transform_option == "LOCROT":
                bpy.ops.object.transform_apply(location = True, rotation = True)
            elif transform_option == "LOCSCALE":
                bpy.ops.object.transform_apply(location = True, scale = True)
            elif transform_option == "ROTSCALE":
                bpy.ops.object.transform_apply(rotation = True, scale = True)
            elif transform_option == "LOC":
                bpy.ops.object.transform_apply(location = True)
            elif transform_option == "ROT":
                bpy.ops.object.transform_apply(rotation = True)
            elif transform_option == "SCALE":
                bpy.ops.object.transform_apply(scale = True)
            bpy.context.scene.objects.active = last_selected
            obj.select = False
            #print("Applied rotation: " + obj.name + " : " + str(obj.rotation_euler))

        if self.export_name == "__DEFAULT__":
            obj["export_name"] = obj.name
        else:
            if self.export_name != "":
                obj["export_name"] = self.export_name
            elif self.original_name != "":
                obj["export_name"] = self.original_name
            else:
                obj["export_name"] = obj.name
    @classmethod
    def unregister(cls):
        try:
            del bpy.types.Object.llexportprops
        except: traceback.print_exc()

class LLObjectPropertiesExportPanel(Panel):
    bl_label = "Export Settings"
    bl_idname = "OBJECT_PT_export_settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    bpy.types.WindowManager.llmergelist_visible = BoolProperty(name="Merging", default=False, description="Select objects to merge when exporting")

    def addon_is_enabled(self, context, addon_name):
        if addon_name in addon_utils.addons_fake_modules:
            default,state = addon_utils.check(addon_name)
            if state:
                return True
        return False

    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    def draw(self, context):
        col = self.layout.row()
        col.label(text="Debug")
        col.operator(AddonDebugOperator.bl_idname)

        col = self.layout.column()
        col.label(text="Export Actions")
        if hasattr(context.object, "llexportprops"):
            context.object.llexportprops.draw(col, context, context.object)

        try:
            if(self.addon_is_enabled(context, "io_scene_dos2de")):
                col = self.layout.column()
                col.label("DOS2DE Collada Settings")
                import io_scene_dos2de
                col.operator(io_scene_dos2de.DOS2DEExtraFlagsOperator.bl_idname)
            else:
                #print("DOS2DE Collada Addon not found.")
                pass
        except: 
            pass

        return

    def execute(self, context, event):
        print("Export Helpers invoked!")

first_init = True

from bpy.app.handlers import persistent

@persistent
def check_init_data(scene):
    global first_init
    if first_init:
        for obj in scene.objects:
            if obj.llexportprops.initialized == False:
                obj.llexportprops.original_name = obj.name
                if obj.llexportprops.export_name == "__DEFAULT__":
                    obj.llexportprops.export_name = obj.name
                obj.llexportprops.initialized = True
        first_init = False
    
    if scene.objects.active is not None:
        obj = scene.objects.active
        if obj.llexportprops.initialized == False:
                obj.llexportprops.original_name = obj.name
                if obj.llexportprops.export_name == "__DEFAULT__":
                    obj.llexportprops.export_name = obj.name
                obj.llexportprops.initialized = True
        else:
            if obj.name != obj.llexportprops.original_name:
                if obj.llexportprops.export_name == obj.llexportprops.original_name:
                    obj.llexportprops.export_name = obj.name
                obj.llexportprops.original_name = obj.name

def register():
    bpy.app.handlers.scene_update_post.append(check_init_data)

def unregister():
    bpy.app.handlers.scene_update_post.remove(check_init_data)

if __name__ == "__main__":
    register()