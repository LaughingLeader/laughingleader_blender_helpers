# class VIEW3D_MT_ParentMenu(Menu):
#     bl_label = "Parent"

#     def draw(self, context):
#         layout = self.layout

#         layout.operator("object.parent_set", text="Set")
#         layout.operator("object.parent_clear", text="Clear")
import bpy
from bpy.types import Operator, AddonPreferences, PropertyGroup, UIList, Panel, Menu
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty
from mathutils import Matrix

from . import leader

class LEADER_ActionEntry(PropertyGroup):
    name = StringProperty()

# def get_actions(scene, context):

#     actions = [("NONE", "None", "")]
#     for action in context.data.actions:
#         actions.append((action.name, action.name, action.name))

#     return actions

def set_visible_animation_can_apply(settings, obj, scene):
    if leader.is_visible(scene, obj) == False:
        return False
    if settings.set_action_active_only == False:
        return True
    else:
        return obj.select == True or scene.objects.active == obj

set_visible_animation_skip = False

def set_visible_animation(settings, context):
    global set_visible_animation_skip
    if set_visible_animation_skip == False:
        action = settings.set_action
        for arm in [x for x in context.scene.objects if (x.type == "ARMATURE" 
            and set_visible_animation_can_apply(settings, x, context.scene))]:
                try:
                    if hasattr(arm, "animation_data") and arm.animation_data != None:
                        pass
                    else:
                        print("[LeaderHelpers] Created animation data for '{}'.".format(arm.name))
                        arm.animation_data_create()

                    if action != "" and action != None:
                        arm.animation_data.action = bpy.data.actions.get(action)
                        print("[LeaderHelpers] Active action set to '{}'.".format(action))
                    else:
                        arm.animation_data.action = None
                        # Reset Pose
                        # Source: https://blender.stackexchange.com/a/147342
                        for pb in arm.pose.bones:
                            pb.matrix_basis = Matrix()
                        print("[LeaderHelpers] Reset pose for '{}'.".format(arm.name))
                except: pass
    else:
        set_visible_animation_skip = False

class LEADER_PROP_ui_misc_settings(PropertyGroup):
    use_replace_existing = BoolProperty(
        name="Replace Existing Armature Modifiers",
        description="Replacing existing armature modifiers values instead of creating new ones",
        default=True
    )

    set_action = StringProperty(
        name="Set Animation",
        description="Set the action to use for visible armatures",
        update=set_visible_animation
    )

    set_action_active_only = BoolProperty(
        name="Active Only",
        description="Only apply selected animations to selected/active armatures",
        default=False
    )

class LEADER_OT_view3d_set_armature_modifier(Operator):
    """Set the armature modifier of selected meshes to the active armature"""
    bl_label = "Set Armature Modifiers to Selected"
    bl_idname = "leader.view3d_set_armature_modifier"
    bl_options = {"REGISTER", "UNDO"}

    use_replace_existing = BoolProperty()

    @classmethod
    def poll(cls, context):
        return (bpy.context.active_object is not None and bpy.context.active_object.type == "ARMATURE" 
            and any(x.type == "MESH" for x in bpy.context.selected_objects))

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "use_replace_existing", text="Replace")
    
    def execute(self, context):
        
        armature = context.active_object

        selected = [obj for obj in context.scene.objects if obj.select == True and obj != armature]
        for obj in selected:
            create_new = False
            armature_modifiers = [mod for mod in obj.modifiers if mod.type == "ARMATURE"]
            if len(armature_modifiers) > 0:
                if self.use_replace_existing:
                    for mod in armature_modifiers:
                        mod.object = armature
                        mod.name = armature.name
                else:
                    create_new = True
            else:
                create_new = True
            
            if create_new:
                mod = obj.modifiers.new(armature.name, "ARMATURE")
                if hasattr(mod, "object"):
                    mod.object = armature
                else:
                    print("[LeaderHelpers] Error adding armature modifier: {}".format(dir(mod)))

        return {'FINISHED'}

    def invoke(self, context, _event):
        return self.execute(context)

class LEADER_OT_view3d_armature_toggle_mode(Operator):
    """Toggle all visible armatures between pose/rest mode"""
    bl_label = "Toggle Pose/Rest Mode"
    bl_idname = "leader.view3d_armature_toggle_mode"
    bl_options = {"UNDO"}

    set_to_pose_mode = BoolProperty()

    @classmethod
    def poll(cls, context):
        for obj in [x for x in context.scene.objects if x.type == "ARMATURE"]:
            if leader.is_visible(context.scene, obj):
                return True
        return False
    
    def execute(self, context):
        for arm in [x for x in context.scene.objects if x.type == "ARMATURE" and leader.is_visible(context.scene, x)]:
            if self.set_to_pose_mode:
                bpy.data.armatures[arm.name].pose_position = "POSE"
            else:
                bpy.data.armatures[arm.name].pose_position = "REST"

        return {'FINISHED'}

    def invoke(self, context, _event):
        return self.execute(context)

arm_valid_modes = ["OBJECT", "POSE", "EDIT_ARMATURE", "EDIT_MESH", "PAINT_WEIGHT"]

class LEADER_PT_view3d_tools_relations_armature_helpers(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Helpers"
    #bl_context = "objectmode"
    bl_label = "Armature Helpers"

    @classmethod
    def poll(cls, context):
        return context.mode in arm_valid_modes

    def draw(self, context):

        layout = self.layout
        settings = getattr(context.scene, "leader_ui_misc_settings", None)

        row = layout.row()
        row.label("Set Armature Position:")
        row = layout.row()
        col = row.column(align=True)
        op = col.operator(LEADER_OT_view3d_armature_toggle_mode.bl_idname, text="Pose")
        op.set_to_pose_mode = True
        col = row.column(align=True)
        op = col.operator(LEADER_OT_view3d_armature_toggle_mode.bl_idname, text="Rest")
        op.set_to_pose_mode = False

        use_replace_existing = settings.use_replace_existing if settings is not None else True
        row = layout.row()
        col = row.column()
        optext = ("Set Armature Modifiers to Active" if 
                len([obj for obj in context.scene.objects if obj.select == True and obj != context.active_object]) > 1 
                    else "Set Armature Modifier to Active")
        op = col.operator(LEADER_OT_view3d_set_armature_modifier.bl_idname, text=optext)
        op.use_replace_existing = use_replace_existing

def removeEmptyGroups(obj, maxWeight = 0):
    valid_groups = []
    total_removed = 0

    for v in obj.data.vertices:
        for g in v.groups:
            #print("[LeaderHelpers] Vertex group weight = '{}'".format(g.weight))
            if g.weight > maxWeight:
                if g not in valid_groups:
                    valid_groups.append(obj.vertex_groups[g.group])

    for r in obj.vertex_groups:
        #print("[LeaderHelpers] Vertex Group [{}] Valid = '{}'".format(r.name, r in valid_groups))
        if r not in valid_groups:
            obj.vertex_groups.remove(r)
            total_removed = total_removed + 1
    return total_removed

def removeZeroVerts(obj, maxWeight = 0):
    total_removed = 0
    for v in obj.data.vertices:
        empty_groups = []
        for g in v.groups:
            if not g.weight > maxWeight:
                empty_groups.append(g)
        for x in empty_groups:
            obj.vertex_groups[x.group].remove([v.index])
            total_removed += 1
    return total_removed

class LEADER_OT_view3d_mesh_clear_emptyvertexgroups(Operator):
    """Remove vertex groups whose total weight is 0"""
    bl_label = "Clear Vertex Groups with Empty Weight"
    bl_idname = "leader.view3d_mesh_clear_emptyvertexgroups"
    bl_options = {"REGISTER", "UNDO"}

    use_remove_empty_groups = BoolProperty(default=True)
    use_remove_zero_verts = BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and context.active_object.type == "MESH"
            and len(context.active_object.vertex_groups) > 0)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, "use_remove_empty_groups", text="Remove Empty Groups")
        row = layout.row()
        row.prop(self, "use_remove_zero_verts", text="Remove Zero Weight Vertices")
    
    def execute(self, context):
        if self.use_remove_empty_groups == False and self.use_remove_zero_verts == False:
            return {'CANCELLED'}

        mesh = context.active_object
        last_mode = None
        if mesh.mode == 'EDIT':
            last_mode = mesh.mode
            bpy.ops.object.mode_set()

        total_groups_removed = 0
        total_verts_removed = 0

        if self.use_remove_empty_groups:
            total_groups_removed += removeEmptyGroups(mesh)

        if self.use_remove_zero_verts:
            total_verts_removed += removeZeroVerts(mesh)
        
        mesh.data.update()

        if last_mode:
            bpy.ops.object.mode_set(mode=last_mode)

        message = "[LeaderHelpers] Removed '{}' vertex groups, '{}' empty vertices.".format(total_groups_removed, total_verts_removed)
        print(message)
        self.report({"INFO"}, message)

        return {'FINISHED'}

    def invoke(self, context, _event):
        return self.execute(context)

class LEADER_PT_view3d_tools_mesh_helpers(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Helpers"
    #bl_context = "objectmode"
    bl_label = "Mesh Helpers"

    @classmethod
    def poll(cls, context):
        return context.mode in arm_valid_modes

    def draw(self, context):

        layout = self.layout
        settings = getattr(context.scene, "leader_ui_misc_settings", None)

        row = layout.row()
        row.operator(LEADER_OT_view3d_mesh_clear_emptyvertexgroups.bl_idname)

#class LEADER_PT_weightpaint_tools_mesh_helpers(LEADER_PT_view3d_tools_mesh_helpers):
#    bl_space_type = 'WEIGHT_PAINT'

class LEADER_OT_timeline_anim_switch(Operator):
    """Switch to the next/previous animation"""
    bl_label = ""
    bl_idname = "leader.timeline_anim_switch"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return len(bpy.data.actions) > 0

    def execute(self, context):
        current_action = context.scene.leader_ui_misc_settings.set_action
        next_action = None
        index = bpy.data.actions.find(current_action)
        if self.forward == True:
            if index >= len(bpy.data.actions) - 1:
                index = -1
            index += 1
        else:
            if index <= 0:
                index = len(bpy.data.actions)
            index -= 1
        
        try:
            next_action = bpy.data.actions[index]
        except:
            next_action = None
 
        if next_action is not None:
            context.scene.leader_ui_misc_settings.set_action = next_action.name
            print("[LeaderHelpers] Set visible armature action to [{}]'{}'.".format(index, next_action.name))

        return {'FINISHED'}

    def invoke(self, context, _event):
        return self.execute(context)

class LEADER_OT_timeline_anim_switch_forward(LEADER_OT_timeline_anim_switch):
    """Switch to the next animation"""
    bl_idname = "leader.timeline_anim_switch_forward"
    forward = BoolProperty(default=True)

class LEADER_OT_timeline_anim_switch_backward(LEADER_OT_timeline_anim_switch):
    """Switch to the previous animation"""
    bl_idname = "leader.timeline_anim_switch_backward"
    forward = BoolProperty(default=False)

def draw_animation_dropdown(self, context):
    row = self.layout.row(align=True)
    #row.label("Set Animation: ")
    row.separator()
    row.operator(LEADER_OT_timeline_anim_switch_backward.bl_idname, text="", icon="BACK")
    row.prop_search(context.scene.leader_ui_misc_settings, "set_action", bpy.data, "actions", text="")
    row.operator(LEADER_OT_timeline_anim_switch_forward.bl_idname, text="", icon="FORWARD")
    row.prop(context.scene.leader_ui_misc_settings, property="set_action_active_only")

from bpy.app.handlers import persistent

last_active_layer = None

def get_action(obj):
    anim_data = getattr(obj, "animation_data", None)
    if anim_data is not None:
        return getattr(anim_data, "action", None)
    return None

@persistent
def update_current_action(scene):
    global last_active_layer
    if last_active_layer != scene.active_layer:
        for obj in [x for x in scene.objects if x.type == "ARMATURE"]:
            action = get_action(obj)
            if action is not None and set_visible_animation_can_apply(scene.leader_ui_misc_settings, obj, scene):
                print("[LeaderHelpers] Setting action in dropdown to [{}] => '{}'.".format(obj.name, obj.animation_data.action.name))
                global set_visible_animation_skip
                set_visible_animation_skip = True
                scene.leader_ui_misc_settings.set_action = obj.animation_data.action.name
                break
        last_active_layer = scene.active_layer

def register():
    try: 
        bpy.types.Scene.leader_ui_misc_settings = PointerProperty(type=LEADER_PROP_ui_misc_settings, 
            name="LeaderHelpers UI Misc Settings",
            description="Miscellaneous settings for various UI helpers"
        )
        bpy.types.TIME_HT_header.append(draw_animation_dropdown)
        bpy.app.handlers.scene_update_post.append(update_current_action)
    except: pass

def unregister():
    try: 
        #del bpy.types.Scene.leader_ui_misc_settings
        bpy.types.TIME_HT_header.remove(draw_animation_dropdown)
        bpy.app.handlers.scene_update_post.remove(update_current_action)
    except: pass

if __name__ == "__main__":
    register()
                