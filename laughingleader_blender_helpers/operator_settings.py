import bpy
from bpy.types import Operator, AddonPreferences, PropertyGroup, UIList, Panel, Menu
from bpy.props import StringProperty, BoolProperty, FloatProperty, EnumProperty, CollectionProperty, PointerProperty, IntProperty

from . import leader

def add(entry):
	leader_operator_settings = getattr(bpy.context.scene, "leader_operator_settings", None)
	if leader_operator_settings is not None:
		leader_operator_settings.add(entry)

toggled_settings = {}

class LEADER_operator_draw_objects(PropertyGroup):
    entries = []

    count = IntProperty(
        default=0,
        name="Total Draw Functions",
        description="The total number of draw functions for the operator settings panels. These are added by other addons"
    )

    def add(self, entry):
        self.entries.append(entry)
        self.count += 1
	
    def draw(self, context, layout):
        if len(self.entries) > 0:
            global toggled_settings
            for entry in self.entries:
                try:
                    draw_func = getattr(entry, "draw", None)
                    toggled = getattr(entry, "toggled", None)
                    name = getattr(entry, "bl_label", "Operator")
                    bl_id = getattr(entry, "bl_id", name)

                    if not bl_id in toggled_settings.keys():
                        toggled_settings[bl_id] = toggled
                        toggled = False

                    if draw_func is not None and toggled is not None:
                        #row = layout.row()
                        layout.prop(entry, "toggled", text=name, toggle=True)
                        if entry.toggled:
                            draw_func(layout, context)
                except Exception as e:
                    print("Error drawing entry: {}".format(e.with_traceback()))

# class LEADER_PT_view3d_operator_settings(Panel):
#     bl_space_type = 'VIEW_3D'
#     bl_region_type = 'TOOLS'
#     bl_category = "Operators"
#     #bl_context = "objectmode"
#     bl_label = "Settings"

#     @classmethod
#     def poll(cls, context):
#         return getattr(context.scene, "leader_operator_settings", None) is not None

#     def draw(self, context):
#         layout = self.layout
#         opsettings = getattr(context.scene, "leader_operator_settings", None)
#         if opsettings is not None:
#             try:
#                 opsettings.draw(context, layout)
#             except Exception as ex:
#                 print("Error drawing operator settings: {}".format(ex.with_traceback()))

def register():
    # bpy.types.Scene.leader_operator_settings = PointerProperty(type=LEADER_operator_draw_objects, 
    #         name="LeaderHelpers Operator Draw Functions",
	# 		options={"HIDDEN"}
    # )
    pass

def unregister():
    # try:
    #     del bpy.types.Scene.leader_operator_settings
    # except: pass
    pass