import bpy
from bpy.types import Operator, PropertyGroup, UIList, Panel
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty

from . import leader

class LEADER_PG_camera_layers_layerdata(PropertyGroup):
    
    enabled = BoolProperty(default=False)

    name = StringProperty(default="LayerData")
    layer_index = IntProperty(default=-1)

    # Object Transforms
    location_x = FloatProperty(default=0)
    location_y = FloatProperty(default=0)
    location_z = FloatProperty(default=0)

    rotation_euler_x = FloatProperty(default=0)
    rotation_euler_y = FloatProperty(default=0)
    rotation_euler_z = FloatProperty(default=0)

    rotation_quaternion_w = FloatProperty(default=1.0)
    rotation_quaternion_x = FloatProperty(default=0)
    rotation_quaternion_y = FloatProperty(default=0)
    rotation_quaternion_z = FloatProperty(default=0)

    rotation_axis_angle_w = FloatProperty(default=0.0)
    rotation_axis_angle_x = FloatProperty(default=0)
    rotation_axis_angle_y = FloatProperty(default=1.0)
    rotation_axis_angle_z = FloatProperty(default=0.0)

    rotation_mode = StringProperty(default="QUATERNION")

    scale_x = FloatProperty(default=0)
    scale_y = FloatProperty(default=0)
    scale_z = FloatProperty(default=0)

    # Camera Properties
    #PERSP, ORTHO, PANO
    camera_type = StringProperty(default="PERSP")
    lens = FloatProperty(default=35.0)
    shift_x = FloatProperty(default=0)
    shift_y = FloatProperty(default=0)
    clip_start = FloatProperty(default=0.1)
    clip_end = FloatProperty(default=100.0)

    def copy_properties(self, obj):
        self.rotation_mode = obj.rotation_mode
    #if obj.rotation_mode == "QUATERNION":
        self.rotation_quaternion_w = obj.rotation_quaternion[0]
        self.rotation_quaternion_x = obj.rotation_quaternion[1]
        self.rotation_quaternion_y = obj.rotation_quaternion[2]
        self.rotation_quaternion_z = obj.rotation_quaternion[3]
    #elif obj.rotation_mode == "AXIS_ANGLE":
        self.rotation_axis_angle_w = obj.rotation_quaternion[0]
        self.rotation_axis_angle_x = obj.rotation_quaternion[1]
        self.rotation_axis_angle_y = obj.rotation_quaternion[2]
        self.rotation_axis_angle_z = obj.rotation_quaternion[3]
    #else: #Euler
        self.rotation_euler_x = obj.rotation_euler[0]
        self.rotation_euler_y = obj.rotation_euler[1]
        self.rotation_euler_z = obj.rotation_euler[2]

        self.location_x = obj.location[0]
        self.location_y = obj.location[1]
        self.location_z = obj.location[2]

        self.scale_x = obj.scale[0]
        self.scale_y = obj.scale[1]
        self.scale_z = obj.scale[2]

        self.camera_type = obj.data.type
        self.lens = obj.data.lens
        self.shift_x = obj.data.shift_x
        self.shift_y = obj.data.shift_y
        self.clip_start = obj.data.clip_start
        self.clip_end = obj.data.clip_end

        self.enabled = True
    
    def apply_properties(self, obj):
        if self.enabled == False:
            return
        obj.rotation_mode = self.rotation_mode
        obj.rotation_quaternion[0] = self.rotation_quaternion_w
        obj.rotation_quaternion[1] = self.rotation_quaternion_x
        obj.rotation_quaternion[2] = self.rotation_quaternion_y
        obj.rotation_quaternion[3] = self.rotation_quaternion_z
        obj.rotation_quaternion[0] = self.rotation_axis_angle_w
        obj.rotation_quaternion[1] = self.rotation_axis_angle_x
        obj.rotation_quaternion[2] = self.rotation_axis_angle_y
        obj.rotation_quaternion[3] = self.rotation_axis_angle_z
        obj.rotation_euler[0] = self.rotation_euler_x
        obj.rotation_euler[1] = self.rotation_euler_y
        obj.rotation_euler[2] = self.rotation_euler_z

        obj.location[0] = self.location_x
        obj.location[1] = self.location_y
        obj.location[2] = self.location_z

        obj.scale[0] = self.scale_x
        obj.scale[1] = self.scale_y
        obj.scale[2] = self.scale_z

        obj.data.type = self.camera_type
        obj.data.lens = self.lens
        obj.data.shift_x = self.shift_x
        obj.data.shift_y = self.shift_y
        obj.data.clip_start = self.clip_start
        obj.data.clip_end = self.clip_end

class LEADER_PG_camera_layers_collection(PropertyGroup):
    data = CollectionProperty(type=LEADER_PG_camera_layers_layerdata)
    active_index = IntProperty(default=0)
    original_data = PointerProperty(type=LEADER_PG_camera_layers_layerdata)

class LEADER_UL_camera_layers_datalist(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, "enabled", text="Enabled", emboss=False)
            layout.prop(item, "layer_index", text="Layer", emboss=False)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

class LEADER_OT_camera_layers_add(bpy.types.Operator):
    """Copies the current camera transforms for the active layer"""
    bl_idname = "llhelpers.camera_adddataforlayer"
    bl_label = "Add"
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.camera

    def execute(self, context):
        obj = context.object
        data = context.object.data
        
        if hasattr(data, "leader_camera_layersettings"):
            layer_index = -1
            for i in range(20):
                if obj.layers[i] == True:
                    print("Copied original transforms to layer {}".format(i))
                    if data.leader_camera_layersettings.original_data.enabled == False:
                        data.leader_camera_layersettings.original_data.layer_index = i
                        data.leader_camera_layersettings.original_data.copy_properties(obj)
                        
                elif context.scene.layers[i] == True:
                    layer_index = i
                    print("Adding data for layer {}".format(i))
                    break

            if layer_index == -1:
                print("No active layers")
                return {'CANCELLED'}
            else:
                layerdata = data.leader_camera_layersettings.data.add()
                layerdata.layer_index = layer_index
                layerdata.copy_properties(obj)
                return {'FINISHED'}
        else:
            print("No leader_camera_layersettings in camera data")
            return {'ERROR'}
        

class LEADER_PT_camera_layers_datapanel(Panel):
    bl_label = "Layer Settings"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.camera

    def draw(self, context):
        obj = context.object        
        layout = self.layout
        row = layout.row()
        row.template_list("LEADER_UL_camera_layers_datalist", "", obj.data.leader_camera_layersettings, "data", 
            obj.data.leader_camera_layersettings, "active_index")
        
        row = layout.row()
        row.operator(LEADER_OT_camera_layers_add.bl_idname)

    def execute(self, context, event):
        print("Export Helpers invoked!")

def register():
    bpy.types.Camera.leader_camera_layersettings = PointerProperty(type=LEADER_PG_camera_layers_collection)
    #bpy.utils.register_class(DATA_PT_llhelpers_selection_groups)
    return

def unregister():
    try:
        del bpy.types.Camera.leader_camera_layersettings
    except: pass
    return

if __name__ == "__main__":
    register()