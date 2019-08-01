import bpy
from bpy.types import Operator, AddonPreferences, PropertyGroup, UIList, Panel
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty

import re

class LLPoseHelpers_MirrorOperator(Operator):
    """"""
    bl_label = "Mirror Pose Movements on the X-Axis"
    bl_idname = "llhelpers.pose_mirroroperator"

    @classmethod
    def poll(cls, context):
        return True
        #obj = context.active_object
        #return (obj is not None and obj.mode == 'POSE')

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, _event):
        return self.execute(context)

def mirror_axis(self, context):
    layout = self.layout
    arm = context.active_object.data
    if arm.llpose_mirror_x_axis:
        layout.operator(LLPoseHelpers_MirrorOperator.bl_idname)

def mirror_get_sideless_name(bone):
    regex = r"(.*?)(_+)(L|R)(_*?.*)"
    subst = "\\1\\4" # Strip out underscores and side indicators (_L_, _R_, etc)

    result = re.sub(regex, subst, bone.name, 1, re.IGNORECASE)

    if result:
        return result
    return False

def mirror_needed(bone, other_bone):
    if other_bone.location != bone.location:
        return True
    elif other_bone.scale != bone.scale:
        return True
    elif other_bone.rotation_mode == bone.rotation_mode:
        if bone.rotation_mode == "QUATERNION":
            return other_bone.rotation_quaternion != bone.rotation_quaternion
        elif bone.rotation_mode == "AXIS_ANGLE":
            return other_bone.rotation_axis_angle != bone.rotation_axis_angle
        else:
            return other_bone.rotation_euler != bone.rotation_euler
    return False

def mirror_rotations(bone, other_bone):
    if other_bone.rotation_mode == bone.rotation_mode:
        if bone.rotation_mode == "QUATERNION":
            other_bone.rotation_quaternion = bone.rotation_quaternion
        elif bone.rotation_mode == "AXIS_ANGLE":
            other_bone.rotation_axis_angle = bone.rotation_axis_angle
        else:
            other_bone.rotation_euler = bone.rotation_euler
    return

def mirror_bone(bone, obj, arm, scene):
    sideless_name = mirror_get_sideless_name(bone)
    if sideless_name is not False:
        reverse_name = ""
        for other_bone in arm.bones:
            if other_bone.name == bone.name:
                continue
            other_sideless_name = mirror_get_sideless_name(other_bone)
            if sideless_name == other_sideless_name:
                reverse_name = other_bone.name
                break
        if reverse_name != "":
            other_pose_bone = obj.pose.bones[reverse_name]
            if other_pose_bone is not None and mirror_needed(bone, other_pose_bone):
                other_pose_bone.location = bone.location
                mirror_rotations(bone, other_pose_bone)
                other_pose_bone.scale = bone.scale
                #print("Mirroring bone: {} {}|{}".format(other_bone.name, pose.location, other_pose.location))
                scene.update()

def mirror_axis_scene(scene):
    if scene.objects.active is not None:
        obj = scene.objects.active
        if obj.type == "ARMATURE" and obj.mode == "POSE":
            arm = obj.data
            if arm.bones.active is not None:
                #bone = arm.bones.active
                for bone in bpy.context.selected_pose_bones:
                    mirror_bone(bone, obj, arm, scene)

appended_update_func = False

def xaxis_mirror_changed(self, context):
    global appended_update_func
    if self.llpose_mirror_x_axis and not appended_update_func:
        bpy.app.handlers.scene_update_post.append(mirror_axis_scene)
        #bpy.types.VIEW3D_MT_pose.append(mirror_axis)
        appended_update_func = True
        print("[LeaderHelpers:PoseHelpers:xaxis_mirror_changed] Appended mirror_axis_scene to bpy.app.handlers.scene_update_post.")
    elif not self.llpose_mirror_x_axis and appended_update_func:
        bpy.app.handlers.scene_update_post.remove(mirror_axis_scene)
        #bpy.types.VIEW3D_MT_pose.remove(mirror_axis)
        appended_update_func = False
        print("[LeaderHelpers:PoseHelpers:xaxis_mirror_changed] Removed mirror_axis_scene from bpy.app.handlers.scene_update_post.")

def mirror_armature_init(scene):
    bpy.app.handlers.scene_update_post.remove(mirror_armature_init)
    if scene.objects is not None:
        for arm in [obj for obj in scene.objects if obj.type == "ARMATURE"]:
            if hasattr(arm.data, "llpose_mirror_x_axis"):
                xaxis_mirror_changed(arm.data, bpy.context)

def render_pose_options(self, context):
    arm = context.active_object.data
    self.layout.prop(arm, "llpose_mirror_x_axis")

classes = (
	LLPoseHelpers_MirrorOperator
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.VIEW3D_PT_tools_posemode_options.append(render_pose_options)
    bpy.types.Armature.llpose_mirror_x_axis = BoolProperty(name="Mirror X Axis", description="Mirror loc/rot/scale posing on opposite bones along the x-axis", default=False, update=xaxis_mirror_changed)
    bpy.app.handlers.scene_update_post.append(mirror_armature_init)

def unregister():
    try:
        bpy.types.VIEW3D_PT_tools_posemode_options.remove(render_pose_options)
        del bpy.types.Armature.llpose_mirror_x_axis
        from bpy.utils import unregister_class
        for cls in reversed(classes):
            unregister_class(cls)
    except: pass

if __name__ == "__main__":
    register()