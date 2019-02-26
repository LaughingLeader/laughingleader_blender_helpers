from __future__ import division
import bpy
from bpy.types import Operator, AddonPreferences, PropertyGroup, UIList
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty

import addon_utils

bl_info = {
    "name": "Export Helpers",
    "author": "LaughingLeader",
    "blender": (2, 7, 9),
    "api": -1,
    "location": "Properties > Export",
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

class LLExportObjectProperty(PropertyGroup):
    name = StringProperty(name="Name", default="", description="")
    selected = BoolProperty(name="Selected", default=False, description="")

class LLExportObjects(PropertyGroup):
    data = CollectionProperty(type=LLExportObjectProperty)
    index = IntProperty()

class LLMergeObjectList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "name")
            layout.prop(item, "selected")

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class LLObjectMergeProperties(bpy.types.PropertyGroup):
    @classmethod
    def register(cls):

        bpy.types.Object.llexportmerge = PointerProperty(
            name="Export Merge Objects",
            description="Objects to merge with when exporting",
            type=cls,
            )

        #Add in the properties you want      
        cls.objects = PointerProperty(
            type=LLExportObjects,
            name="Objects",
            description="Selected objects for merging when exporting",
        )

        cls.objects_initialized = BoolProperty(
            default=False
        )

    def rebuild_objects(self, target_obj, scene):
        self.objects.data.clear()

        target_type = target_obj.type

        for obj in scene.objects:
            if obj.type == target_type and obj.name != target_obj.name:
                obj_data = self.objects.data.add()
                obj_data.name = obj.name

    @classmethod
    def unregister(cls):
        try:
            del bpy.types.Object.llexportmerge
        except: traceback.print_exc()

class LLExportMergeOperator(Operator):
    """Merge with a selected armature when exporting"""
    bl_idname = "llhelpers.export_mergeobjects"
    bl_label = "Merge"

    available_objects = PointerProperty(
        type=LLExportObjects,
        name="Objects",
        description="Available objects for merging when exporting"
    )

    def invoke(self, context, event):
        target_obj = context.object
        target_type = target_obj.type

        already_selected = []

        if target_obj.llexportmerge is not None:
            for obj in target_obj.llexportmerge.objects.data:
                if obj.selected:
                    already_selected.append(obj.name)

        for obj in context.scene.objects:
            if obj.type == target_type and obj.name != target_obj.name:
                obj_data = self.available_objects.data.add()
                obj_data.name = obj.name
                obj_data.select = obj.name in already_selected
        
        wm = context.window_manager
        return wm.invoke_props_dialog(self)
    
    def draw(self, context):
        self.layout.template_list("LLMergeObjectList", "", self.available_objects, "data", self.available_objects, "index")

    def execute(self, context):
        target_obj = context.object

        target_obj.llexportmerge.objects.data.clear()

        for obj in self.available_objects.data:
            new_obj = target_obj.llexportmerge.objects.data.add()
            new_obj.name = obj.name
            new_obj.selected = True

        return {'FINISHED'}

class LLPropertiesExportPanel(bpy.types.Panel):
    bl_label = "Export Settings"
    bl_idname = "OBJECT_PT_export_settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    bpy.types.WindowManager.llmergelist_visible = BoolProperty(name="Merging", default=False, description="Select objects to merge when exporting")

    def addon_is_enabled(self, context, addon_name):
        if addon_name in addon_utils.addons_fake_modules:
            default, state = addon_utils.check(addon_name)
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

        wm = context.window_manager
        
        col = self.layout.column()
        #col.label(text="Merge", text_ctxt="Merge with objects on export")
        label = "Merging" if wm.llmergelist_visible else "Merging (Hidden)"
        col.prop(wm, "llmergelist_visible", text=label, toggle=True)
        if wm.llmergelist_visible:
            col.template_list("LLMergeObjectList", "", context.object.llexportmerge.objects, "data", context.object.llexportmerge.objects, "index")
        #col.operator(LLExportMergeOperator.bl_idname)

        if(self.addon_is_enabled(context, "io_scene_dos2de")):
            col = self.layout.column()
            col.label("DOS2DE Collada Settings")
            import io_scene_dos2de
            col.operator(io_scene_dos2de.DOS2DEExtraFlagsOperator.bl_idname)
            
        return

    def execute(self, context, event):
        print("Export Helpers invoked!")

from bpy.app.handlers import persistent

first_init = True

@persistent
def check_init_data(scene):
    global first_init
    if first_init:
        for obj in scene.objects:
            if obj.llexportmerge.objects_initialized == False:
                obj.llexportmerge.rebuild_objects(obj, scene)
                obj.llexportmerge.objects_initialized = True
        first_init = False

def register():
    bpy.app.handlers.scene_update_post.append(check_init_data)

def unregister():
    #bpy.utils.unregister_class(AddonDebugOperator)
    #bpy.utils.unregister_class(LLPropertiesExportPanel)
    return

if __name__ == "__main__":
    register()