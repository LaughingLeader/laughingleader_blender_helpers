import bpy

from bpy.types import Operator, PropertyGroup, UIList, Panel
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty

bl_info = {
    "name": "Export Helpers > Scene",
    "author": "LaughingLeader",
    "blender": (2, 7, 9),
    "api": -1,
    "location": "Toolshelf > Export Tab",
    "description": ("Helpers for customizing file export"),
    "warning": "",
    "wiki_url": (""),
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "3D View"
}

class LLExportObject(PropertyGroup):
    obj = PointerProperty(name="Object", type=bpy.types.Object, options={"HIDDEN"})
    name = StringProperty(name="Name")

class LLObjectMergeProperties(PropertyGroup):
    @classmethod
    def register(cls):
        bpy.types.Scene.llexportmerge = PointerProperty(
            name="Export Merge Objects",
            description="Objects to merge with when exporting",
            type=cls
            )

        cls.active_layers_only = BoolProperty(
            name="Active Layers Only", 
            description="Only show objects on active layers as addable", 
            default=False)
          
        cls.armatures = CollectionProperty(
            type=LLExportObject,
            name="Armatures",
            description="Selected armatures for merging when exporting"
        )
        cls.armatures_index = IntProperty(options={"HIDDEN"})
          
        cls.meshes = CollectionProperty(
            type=LLExportObject,
            name="Meshes",
            description="Selected meshes for merging when exporting"
        )

        cls.meshes_index = IntProperty(options={"HIDDEN"})

        cls.initialized = BoolProperty(
            default=False,
            options={"HIDDEN"}
        )

        # cls.selectable_objects = CollectionProperty(
        #     type=LLExportObject,
        #     name="Selectable Objects",
        #     options={"HIDDEN"}
        # )

    def rebuild_objects(self, scene, objtype):
        if objtype == "armature":
            last_armatures = []
            for entry in self.armatures:
                if entry.obj in scene.objects:
                    last_armatures.append(entry.obj.name)
            self.armatures.clear()
            for obj in scene.objects:
                if obj.type == objtype:
                    if obj.name in last_armatures:
                        obj_data = self.armatures.add()
                        obj_data.obj = obj
                        obj_data.name = obj.name
        if objtype == "mesh":
            last_meshes = []
            for entry in self.meshes:
                if entry.obj in scene.objects:
                    last_meshes.append(entry.obj.name)
            self.meshes.clear()
            for obj in scene.objects:
                if obj.type == objtype:
                    if obj.name in last_meshes:
                        obj_data = self.meshes.add()
                        obj_data.obj = obj
                        obj_data.name = obj.name

    @classmethod
    def unregister(cls):
        import traceback
        try:
            del bpy.types.Scene.llexportmerge
        except: traceback.print_exc()

class LLSceneMergeListActions(Operator):
    bl_idname = "llhelpers.export_merge_listactions"
    bl_label = "Add Object"

    object_type = EnumProperty(
        name="Target Object Type",
        items=(
            ("ARMATURE", "Armature", ""),
            ("MESH", "Mesh", ""),
        ),
        default=("MESH")
    )

    action = EnumProperty(
        items=(
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('REMOVE', "Remove", ""),
            ('ADD', "Add", "")))

    def get_selectables(self, context):
        selectables = []
        for obj in context.scene.objects:
            if obj.type == self.object_type:
                can_add = True

                if context.scene.llexportmerge.active_layers_only:
                    for i in range(20):
                        if context.scene.layers[i]:
                            if not obj.layers[i]:
                                can_add = False
                                break

                if can_add:
                    if self.object_type == "ARMATURE":
                        for objp in context.scene.llexportmerge.armatures:
                            if obj == objp.obj:
                                can_add = False
                                break
                    elif self.object_type == "MESH": 
                        for objp in context.scene.llexportmerge.meshes:
                            if obj == objp.obj:
                                can_add = False
                                break
                if can_add:
                    selectables.append((obj.name, obj.name, obj.name))
        return selectables

    add_object = EnumProperty(
        items=get_selectables
    )

    def execute(self, context):
        for obj in context.scene.objects:
            if obj.name == self.add_object:
                if self.object_type == "ARMATURE":
                    obj_data = context.scene.llexportmerge.armatures.add()
                    obj_data.obj = obj
                    obj_data.name = obj.name
                elif self.object_type == "MESH": 
                    obj_data = context.scene.llexportmerge.meshes.add()
                    obj_data.obj = obj
                    obj_data.name = obj.name
                break
        return {'FINISHED'}

    def update_scene_index(self, scene, add_index):
        if self.object_type == "ARMATURE":
            scene.llexportmerge.armatures_index += add_index
        elif self.object_type == "MESH": 
            scene.llexportmerge.meshes_index += add_index

    def invoke(self, context, event):
        scene = context.scene
        if self.action == "ADD":
            # scene.llexportmerge.selectable_objects.clear()
            # for obj in scene.objects:
            #     if obj.type == self.object_type:
            #         obj_pointer = scene.llexportmerge.selectable_objects.add()
            #         obj_pointer.obj = obj
            #         obj_pointer.name = obj.name
            #         print("Added {}".format(obj.name))
            # print("Set up selectable_objects?")

            wm = context.window_manager
            return wm.invoke_props_dialog(self)
        else:
            objects = None
            index = 0
            if self.object_type == "ARMATURE":
                objects = scene.llexportmerge.armatures
                index = scene.llexportmerge.armatures_index
            elif self.object_type == "MESH": 
                objects = scene.llexportmerge.meshes
                index = scene.llexportmerge.meshes_index

            try:
                item = objects[index]
            except IndexError:
                pass
            else:
                if self.action == 'DOWN' and index < len(objects) - 1:
                    objects.move(index, index+1)
                    self.update_scene_index(scene, 1)
                    info = 'Item "%s" moved to position %d' % (objects[index+1].name, index + 1)
                    self.report({'INFO'}, info)

                elif self.action == 'UP' and index >= 1:
                    objects.move(index, index-1)
                    self.update_scene_index(scene, -1)
                    info = 'Item "%s" moved to position %d' % (objects[index-1].name, index - 1)
                    self.report({'INFO'}, info)

                elif self.action == 'REMOVE':
                    info = 'Item "%s" removed from list' % (objects[index].name)
                    self.update_scene_index(scene, -1)
                    objects.remove(index)
                    self.report({'INFO'}, info)
            return {"FINISHED"}

    def draw(self, context):
        self.layout.prop(self, "add_object")
        #self.layout.prop_search(context.scene.llexportmerge, "addobject", context.scene.llexportmerge, "selectable_objects")

class LLMergeObjectList(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            iconval = "OBJECT_DATA"
            if item.obj.type == "ARMATURE":
                iconval = "OUTLINER_OB_ARMATURE"
            elif item.obj.type == "MESH":
                iconval = "OUTLINER_OB_MESH"
            #layout.prop(item, "name", icon_value=icon)
            layout.label(text=item.name, icon=iconval)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)
            
class LLSceneExportPanel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"
    bl_category = "Export"
    bl_label = "Export Settings"
    #bl_options = {'DEFAULT_CLOSED'}

    bpy.types.WindowManager.llmergelist_visible = BoolProperty(name="Merging", default=False, description="Select objects to merge when exporting")

    def draw_merge_list(self, context, layout, data, objects_var, index_var, label, object_type):

        data_list = getattr(data, objects_var, None)

        is_sortable = data_list is not None and len(data_list) > 0
        rows = 1
        if (is_sortable):
            rows = 4

        layout.label(text=label)
        row = layout.row()
        row.template_list("LLMergeObjectList", "", data, objects_var, data, index_var, rows=rows, type="DEFAULT")

        col = row.column(align=True)
        op = col.operator(LLSceneMergeListActions.bl_idname, icon='ZOOMIN', text="")
        op.object_type = object_type
        op.action = "ADD"
        op = col.operator(LLSceneMergeListActions.bl_idname, icon='ZOOMOUT', text="")
        op.object_type = object_type
        op.action = "REMOVE"

        if is_sortable:
            col.separator()
            op = col.operator(LLSceneMergeListActions.bl_idname, icon='TRIA_UP', text="")
            op.object_type = object_type
            op.action = "UP"
            op = col.operator(LLSceneMergeListActions.bl_idname, icon='TRIA_DOWN', text="")
            op.object_type = object_type
            op.action = "DOWN"

    def draw(self, context):
        wm = context.window_manager
        scene = context.scene

        col = self.layout.column()
        label = "Merging" if wm.llmergelist_visible else "Merging (Hidden)"
        col.prop(wm, "llmergelist_visible", text=label, toggle=True)
        if wm.llmergelist_visible:
            col.prop(scene.llexportmerge, "active_layers_only")
            col = self.layout.column()
            self.draw_merge_list(context, col, scene.llexportmerge, "armatures", "armatures_index", "Armatures", "ARMATURE")
            #col = self.layout.column()
            self.draw_merge_list(context, col, scene.llexportmerge, "meshes", "meshes_index", "Meshes", "MESH")
        return

    def execute(self, context, event):
        print("Export Helpers invoked!")

first_init = True

from bpy.app.handlers import persistent

@persistent
def check_init_data(scene):
    global first_init
    if first_init:
        if scene.llexportmerge.initialized == False:
                scene.llexportmerge.rebuild_objects(scene, "armature")
                scene.llexportmerge.rebuild_objects(scene, "mesh")
                scene.llexportmerge.initialized = True
        first_init = False

def register():
    bpy.app.handlers.scene_update_post.append(check_init_data)

def unregister():
    bpy.app.handlers.scene_update_post.remove(check_init_data)