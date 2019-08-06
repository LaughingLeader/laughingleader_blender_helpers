# class VIEW3D_MT_ParentMenu(Menu):
#     bl_label = "Parent"

#     def draw(self, context):
#         layout = self.layout

#         layout.operator("object.parent_set", text="Set")
#         layout.operator("object.parent_clear", text="Clear")
import bpy
from bpy.types import Operator, AddonPreferences, PropertyGroup, UIList, Panel, Menu
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty

from . import leader

class LEADER_ActionEntry(PropertyGroup):
    name = StringProperty()

# def get_actions(scene, context):

#     actions = [("NONE", "None", "")]
#     for action in context.data.actions:
#         actions.append((action.name, action.name, action.name))

#     return actions
    
def set_visible_animation(settings, context):
    action = settings.set_action
    if action != "" and action in bpy.data.actions:
        for arm in [x for x in context.scene.objects if x.type == "ARMATURE" and leader.is_visible(context.scene, x)]:
            arm.animation_data.action = bpy.data.actions.get(action)
        #context.operator.report("Active action set to '{}'.".format(action))

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

class LEADER_OT_timeline_anim_switch(Operator):
    """Switch to the next/previous animation"""
    bl_label = ""
    bl_idname = "leader.timeline_anim_switch"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return True

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
        next_action = bpy.data.actions[index]
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
    row.operator(LEADER_OT_timeline_anim_switch_backward.bl_idname, text="", icon="BACK")
    row.prop_search(context.scene.leader_ui_misc_settings, "set_action", bpy.data, "actions", text="")
    row.operator(LEADER_OT_timeline_anim_switch_forward.bl_idname, text="", icon="FORWARD")

from bpy.app.handlers import persistent

last_active_layer = None

@persistent
def update_current_action(scene):
    global last_active_layer
    if last_active_layer != scene.active_layer:
        for obj in [x for x in scene.objects if x.type == "ARMATURE"]:
            if leader.is_visible(scene, obj) and obj.animation_data.action is not None:
                scene.leader_ui_misc_settings.set_action = obj.animation_data.action.name
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
                