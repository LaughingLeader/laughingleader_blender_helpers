import bpy
from bpy.types import Operator, AddonPreferences, PropertyGroup, UIList, Panel
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty

class LLPoseHelpers_MirrorOperator(Operator):
    """Extrude each individual face separately along local normals"""
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

def render_pose_options(self, context):
    arm = context.active_object.data
    self.layout.prop(arm, "llpose_mirror_x_axis")

def mirror_axis(self, context):
    layout = self.layout
    arm = context.active_object.data
    if arm.llpose_mirror_x_axis:
        layout.operator(LLPoseHelpers_MirrorOperator.bl_idname)

def mirror_side_match(bone, side):
    side_check = "_{}_".format(side)
    if side_check in bone.name:
        return side_check
    side_check = "_{}".format(side)
    if side_check in bone.name:
        return side_check
    return False

def mirror_get_side(bone):
    side = mirror_side_match(bone, "L")
    if side is False:
        side = mirror_side_match(bone, "R")
        if side is not False:
            return side
        else:
            return False
    else:
        return side

def mirror_bone(bone, obj, arm, scene):
    side = mirror_get_side(bone)
    if side is not False:
        if "L" in side:
            reverse_side = str.replace(side, "L", "R", 1)
        else:
            reverse_side = str.replace(side, "R", "L", 1)
        reverse_name = str.replace(bone.name, side, reverse_side, 1)
        other_bone_index = arm.bones.find(reverse_name)
        if other_bone_index != -1:
            other_bone = obj.pose.bones[reverse_name]
            if other_bone is not None and other_bone.location != bone.location:
                other_bone.location = bone.location
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

def register():
    bpy.types.VIEW3D_PT_tools_posemode_options.append(render_pose_options)
    bpy.types.Armature.llpose_mirror_x_axis = BoolProperty(name="Mirror X Axis", description="Mirror posing on similar bones along the x-axis", default=False, update=xaxis_mirror_changed)

def unregister():
    try:
        bpy.types.VIEW3D_PT_tools_posemode_options.remove(render_pose_options)
        del bpy.types.Armature.llpose_mirror_x_axis
    except: pass

if __name__ == "__main__":
    register()