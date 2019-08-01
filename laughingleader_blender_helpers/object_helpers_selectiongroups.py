import bpy
import bmesh
from bpy.utils import register_class
from bpy.utils import unregister_class
from bpy.types import (
        Operator,
        Panel,
        Menu,
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

class LLObjectSelectionGroup(PropertyGroup):
    group_id = StringProperty(options={"HIDDEN"})
    name = StringProperty(
            name="Name",
            description="The name of the selection group",
            default="Group"
        )
    lock = BoolProperty(name="Lock", default=False)

class LLObjectSelectionGroupProperties(PropertyGroup):
   
    groups = CollectionProperty(
            type=LLObjectSelectionGroup,
            name="Groups",
            description="All selection groups")

    active_index = IntProperty(options={"HIDDEN"})

class LLHelpers_UL_SelectionGroups(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        group = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(group, "name", text="", emboss=False, icon_value=icon)
            icon = 'LOCKED' if group.lock else 'UNLOCKED'
            layout.prop(group, "lock", text="", icon=icon, emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class LLObjectSelectionGroup_AddOperator(bpy.types.Operator):
    """Add a new selection group"""
    bl_idname = "llhelpers.object_selectiongroup_add"
    bl_label = "Add"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        if hasattr(context.object, "llselectiongroups"):
            
            total_groups = 0
            for group in context.object.llselectiongroups.groups:
                total_groups += 1
            
            if total_groups == 0:
                total_groups = 1
            
            new_group = context.object.llselectiongroups.groups.add()
            new_group.name = "Group{}".format(total_groups)

            import uuid
            new_group.group_id = str((uuid.uuid4().int>>64))
        
        return {'FINISHED'}


class LLObjectSelectionGroup_RemoveOperator(bpy.types.Operator):
    """Remove the selected group"""
    bl_idname = "llhelpers.object_selectiongroup_remove"
    bl_label = "Remove"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type in {'MESH', 'LATTICE'} and len(obj.llselectiongroups.groups) > 0)

    def execute(self, context):
        if context.object.llselectiongroups.active_index > -1:
            context.object.llselectiongroups.groups.remove(context.object.llselectiongroups.active_index)
        
        return {'FINISHED'}

class LLObjectSelectionGroup_MoveOperatorBase(bpy.types.Operator):
    bl_idname = "llhelpers.object_selectiongroup_movebase"
    bl_label = ""
    direction = ""
    
    @classmethod
    def poll(cls, context):
        obj = context.object
        if (obj and obj.type in {'MESH', 'LATTICE'} and len(obj.llselectiongroups.groups) > 0):
            #print("Index:{} Direction: {}".format(obj.llselectiongroups.active_index, cls.direction.get()))
            if cls.direction == "UP" and obj.llselectiongroups.active_index > 0:
                return True
            elif cls.direction == "DOWN" and obj.llselectiongroups.active_index < len(obj.llselectiongroups.groups) - 1:
                return True
        return False

    def execute(self, context):
        obj = context.object
        index = obj.llselectiongroups.active_index
        target_index = index
        groups = obj.llselectiongroups.groups
        if self.direction == 'DOWN' and index < len(groups) - 1:
            target_index = index+1
            groups.move(index, target_index)
        elif self.direction == 'UP' and index >= 1:
            target_index = index-1
            groups.move(index, target_index)
        
        obj.llselectiongroups.active_index = target_index

        return {'FINISHED'}

class LLObjectSelectionGroup_MoveUpOperator(LLObjectSelectionGroup_MoveOperatorBase, bpy.types.Operator):
    """Move the selected group up"""
    bl_idname = "llhelpers.object_selectiongroup_moveup"
    bl_label = "Move Up"
    direction = "UP"

class LLObjectSelectionGroup_MoveDownOperator(LLObjectSelectionGroup_MoveOperatorBase, bpy.types.Operator):
    """Move the selected group down"""
    bl_idname = "llhelpers.object_selectiongroup_movedown"
    bl_label = "Move Down"
    direction = "DOWN"

class LLObjectSelectionGroup_AssignOperatorBase(bpy.types.Operator):
    bl_idname = "llhelpers.object_selectiongroup_assignbase"
    bl_label = ""
    mode = ""

    @classmethod
    def poll(cls, context):
        obj = context.object

        active = False

        if (obj and obj.type in {'MESH', 'LATTICE'} and len(obj.llselectiongroups.groups) > 0):
            if obj.llselectiongroups.active_index > -1:
                active = obj.llselectiongroups.groups[obj.llselectiongroups.active_index].lock == False

        return active

    def execute(self, context):
        obj = context.object

        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        group = obj.llselectiongroups.groups[obj.llselectiongroups.active_index]
        group_data = (bm.verts.layers.int.get(group.group_id) or bm.verts.layers.int.new(group.group_id))
        
        for v in bm.verts:
            if v.select:
                v[group_data] = 1 if self.mode == "ADD" else 0

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}

class LLObjectSelectionGroup_AssignOperator(LLObjectSelectionGroup_AssignOperatorBase, bpy.types.Operator):
    """Assign selected vertices to the group"""
    bl_idname = "llhelpers.object_selectiongroup_assign"
    bl_label = "Assign"
    mode = "ADD"

class LLObjectSelectionGroup_UnAssignOperator(LLObjectSelectionGroup_AssignOperatorBase, bpy.types.Operator):
    """Unassign selected vertices in group"""
    bl_idname = "llhelpers.object_selectiongroup_unssign"
    bl_label = "Remove"
    mode = "REMOVE"

class LLObjectSelectionGroup_BaseSelectOperator(bpy.types.Operator):
    bl_idname = "llhelpers.object_selectiongroup_baseselect"
    bl_label = ""
    mode = ""

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type in {'MESH', 'LATTICE'} and len(obj.llselectiongroups.groups) > 0)

    def execute(self, context):
        obj = context.object

        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        group = obj.llselectiongroups.groups[obj.llselectiongroups.active_index]
        group_data = bm.verts.layers.int.get(group.group_id)
        if group_data:
            for v in bm.verts:
                if v[group_data] == 1:
                    v.select = self.mode == "SELECT"
            bm.select_flush_mode()
            bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}
    
class LLObjectSelectionGroup_SelectOperator(LLObjectSelectionGroup_BaseSelectOperator, bpy.types.Operator):
    """Select vertices in the group"""
    bl_idname = "llhelpers.object_selectiongroup_select"
    bl_label = "Select"
    mode = "SELECT"

class LLObjectSelectionGroup_DeselectOperator(LLObjectSelectionGroup_BaseSelectOperator, bpy.types.Operator):
    """Deselect vertices in the group"""
    bl_idname = "llhelpers.object_selectiongroup_deselect"
    bl_label = "Deselect"
    mode = "DESELECT"

class LLObjectSelectionGroups_Panel(bpy.types.Panel):
    bl_label = "Selection Groups"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type in {'MESH', 'LATTICE'})

    def draw(self, context):
        layout = self.layout

        ob = context.object
        group = len(ob.llselectiongroups.groups) > 0

        rows = 2
        if group:
            rows = 4

        row = layout.row()
        row.template_list("LLHelpers_UL_SelectionGroups", "", ob.llselectiongroups, "groups", ob.llselectiongroups, "active_index", rows=rows)

        col = row.column(align=True)
        col.operator(LLObjectSelectionGroup_AddOperator.bl_idname, icon='ZOOMIN', text="")
        props = col.operator(LLObjectSelectionGroup_RemoveOperator.bl_idname, icon='ZOOMOUT', text="")
        #props.all_unlocked = props.all = False
        #col.menu("MESH_MT_vertex_group_specials", icon='DOWNARROW_HLT', text="")
        if group:
            col.separator()
            col.operator(LLObjectSelectionGroup_MoveUpOperator.bl_idname, icon='TRIA_UP', text="")
            col.operator(LLObjectSelectionGroup_MoveDownOperator.bl_idname, icon='TRIA_DOWN', text="")

        if ob.llselectiongroups and (ob.mode == 'EDIT' and ob.type == 'MESH'):
            row = layout.row()

            sub = row.row(align=True)
            sub.operator(LLObjectSelectionGroup_AssignOperator.bl_idname, text="Assign")
            sub.operator(LLObjectSelectionGroup_UnAssignOperator.bl_idname, text="Remove")

            sub = row.row(align=True)
            sub.operator(LLObjectSelectionGroup_SelectOperator.bl_idname, text="Select")
            sub.operator(LLObjectSelectionGroup_DeselectOperator.bl_idname, text="Deselect")

classes = (
	LLObjectSelectionGroup,
	LLObjectSelectionGroupProperties,
	LLHelpers_UL_SelectionGroups,
	LLObjectSelectionGroup_AddOperator,
	LLObjectSelectionGroup_RemoveOperator,
	LLObjectSelectionGroup_MoveOperatorBase,
	LLObjectSelectionGroup_MoveUpOperator,
	LLObjectSelectionGroup_MoveDownOperator,
	LLObjectSelectionGroup_AssignOperatorBase,
	LLObjectSelectionGroup_AssignOperator,
	LLObjectSelectionGroup_UnAssignOperator,
	LLObjectSelectionGroup_BaseSelectOperator,
	LLObjectSelectionGroup_SelectOperator,
	LLObjectSelectionGroup_DeselectOperator,
	LLObjectSelectionGroups_Panel
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Object.llselectiongroups = PointerProperty(type=LLObjectSelectionGroupProperties)
    #bpy.utils.register_class(DATA_PT_llhelpers_selection_groups)

def unregister():
    try:
        del bpy.types.Object.llselectiongroups
    except: pass
    #bpy.utils.unregister_class(DATA_PT_llhelpers_selection_groups)
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()