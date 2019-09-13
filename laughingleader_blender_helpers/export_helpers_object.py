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

class LLExportHelpers_AddonDebugOperator(Operator):
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

class LLExportHelpers_ObjectExportProperties(PropertyGroup):
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
        
        cls.locked = BoolProperty(
            options={"HIDDEN"},
            default=False
        )

        cls.initialized = BoolProperty(
            options={"HIDDEN"},
            default=False
        )

    def draw(self, layout, context, obj):
        layout.prop(self, "export_name")
        layout.prop(self, "apply_transforms")

    def copy(self, target_props, lock=True):
        if "export_name" in target_props:
            self.export_name = target_props.export_name
        if "apply_transforms" in target_props:
            self.apply_transforms = target_props.apply_transforms
        self.locked = lock

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

        if self.export_name == "__DEFAULT__" and self.locked == False:
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
        except: pass

class LLExportHelpers_AddonDrawHandler(PropertyGroup):
    functions = []

    count = IntProperty(
        default=0,
        name="Total Draw Functions",
        description="The total number of draw functions for an object's export properties. These are added by other addons"
    )

    def add(self, draw_func):
        self.functions.append(draw_func)
        self.count += 1
    
    def init(self):
        #self.functions.clear()
        self.count = 0

class LLExportHelpers_ObjectExportPropertiesPanel(Panel):
    bl_label = "Export Settings"
    bl_idname = "llhelpers.export_objectpropertiespanel"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    bpy.types.WindowManager.llmergelist_visible = BoolProperty(name="Merging", default=False, description="Select objects to merge when exporting")

    def addon_is_enabled(self, context, addon_name):
        try:
            default,state = addon_utils.check(addon_name)
            if state:
                return True
        except:
            pass
        return False
 
    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    def draw(self, context):
        #col = self.layout.row()
        #col.label(text="Debug")
        #col.operator(LLExportHelpers_AddonDebugOperator.bl_idname)

        col = self.layout.column()
        col.label(text="Export Actions")
        if hasattr(context.object, "llexportprops"):
            context.object.llexportprops.draw(col, context, context.object)

        try:
            #print("Total functions: {}".format(len(context.scene.llexport_object_drawhandler.functions)))
            if len(context.scene.llexport_object_drawhandler.functions) > 0:
                for draw_func in context.scene.llexport_object_drawhandler.functions:
                    if callable(draw_func):
                        draw_func(self, context)
        except Exception as e:
            print("[LeaderHelpers:ExportHelpers_Object:draw] Error calling draw function:\nError:\n{}".format(e))
        return

    def execute(self, context, event):
        print("Export Helpers invoked!")

first_init = True

from bpy.app.handlers import persistent

@persistent
def check_init_data(scene):
    global first_init
    if first_init:
        scene.llexport_object_drawhandler.init()
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
            if obj.name != obj.llexportprops.original_name and obj.llexportprops.locked == False:
                if obj.llexportprops.export_name == obj.llexportprops.original_name:
                    obj.llexportprops.export_name = obj.name
                obj.llexportprops.original_name = obj.name

def register():
    bpy.types.Scene.llexport_object_drawhandler = PointerProperty(type=LLExportHelpers_AddonDrawHandler, 
            name="LeaderHelpers Export Draw Handlers",
            description="A list of functions other addons can register to in order to draw more properties on the object export panel"
    )
    bpy.app.handlers.scene_update_post.append(check_init_data)

def unregister():
    bpy.app.handlers.scene_update_post.remove(check_init_data)
    try:
        del bpy.types.Scene.llexport_object_drawhandler
    except: pass

if __name__ == "__main__":
    register()