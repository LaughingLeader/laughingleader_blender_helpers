import bpy
import bmesh
import os

from bpy.types import Operator, PropertyGroup
from bpy.props import CollectionProperty, PointerProperty

bl_info = {
    "name": "UV Helpers",
    "author": "LaughingLeader",
    "blender": (2, 7, 9),
    "api": -1,
    "location": "Edit Mode > UV / Image Editor > UVs",
    "description": ("Helpers for cleaning up UVs, checking for errors, and more"),
    "warning": "",
    "wiki_url": (""),
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "UV"
}

class UVError:
    def __init__(self, vert1, vert2, loop1, loop2):
        self.vert1 = vert1
        self.vert2 = vert2
        self.loop1 = loop1
        self.loop2 = loop2

class UVUnwrappedChecker(Operator):
    """Check for unwrapped UVs that will cause tangent/binormal issues.\nThese are UVs from separate vertices that share the exact same UV coordinates for a face."""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "uvhelpers.unwrappedchecker"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Check for Unwrapped UVs"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    def uv_error(self, vert1, vert2, uv1, uv2):
        if vert1 != vert2 and uv1 == uv2:
            return True

    def execute(self, context):        # execute() is called when running the operator.

        # The original script
        scene = context.scene
        node = bpy.context.scene.objects.active

        bpy.ops.object.mode_set(mode="EDIT")

        if node.type == "MESH":
            if (node.data is not None):

                #os.system("cls")

                mesh = node.data

                bm = bmesh.from_edit_mesh(mesh)
                bm.select_mode = {"VERT"}
                bm.select_flush(False)
                uv_layer = bm.loops.layers.uv.active

                uv_errors = []

                for face in bm.faces:
                    for loop in face.loops:
                        vert = loop.vert
                        vert.select_set(False)
                        #loop.select(False)

                        #print("  Vert: (%f,%f,%f)" % vert.co[:])
                        uv_loop = loop[uv_layer]
                        uv = uv_loop.uv
                        #print("    UV: %f, %f" % uv[:])
                        ux = uv[0]
                        uy = uv[1]

                        for checkloop in face.loops:
                            if checkloop == loop:
                                break

                            vert2 = checkloop.vert
                            checkuv_loop = checkloop[uv_layer]
                            checkuv = checkuv_loop.uv

                            if self.uv_error(vert, vert2, uv, checkuv):
                                uv_error_entry = UVError(vert, vert2, uv_loop, checkuv_loop)
                                uv_errors.append(uv_error_entry)

                total_errors = len(uv_errors)
                if total_errors > 0:
                    for uv_error in uv_errors:
                        print("[ERROR]: UV problem detected!")
                        print("  Vert1: (%f,%f,%f)" % uv_error.vert1.co[:])
                        print("  Vert2: (%f,%f,%f)" % uv_error.vert2.co[:])
                        print("  UV1: (%f,%f)" % uv_error.loop1.uv[:])
                        print("  UV2: (%f,%f)" % uv_error.loop2.uv[:])
                        uv_error.vert1.select_set(True)
                        uv_error.vert2.select_set(True)
                        uv_error.loop1.select = True
                        uv_error.loop2.select = True

                    self.report({"WARNING"}, "[LL-UV-Helper] {} total problems found on UV map. Check selected vertices for wrapping issues.".format(total_errors))
                else:
                    self.report({"INFO"}, "[LL-UV-Helper] No UV problems found.")
                    
                bm.select_flush(True)
                bmesh.update_edit_mesh(mesh)
        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

class UVHelperPanel(bpy.types.Panel):
    bl_label = "Helpers"
    bl_idname = "IMAGE_MT_ll_uvhelpers"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = 'Helpers'

    def draw(self, context):
        layout = self.layout

        layout.operator(UVUnwrappedChecker.bl_idname)

def register():
    #bpy.utils.register_class(UVError)
    bpy.utils.register_class(UVUnwrappedChecker)
    bpy.utils.register_class(UVHelperPanel)


def unregister():
    #bpy.utils.unregister_class(UVError)
    bpy.utils.unregister_class(UVUnwrappedChecker)
    bpy.utils.unregister_class(UVHelperPanel)
