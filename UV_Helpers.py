from __future__ import division
import bpy
import bmesh
import os

import math

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

class UVErrorv2:
    def __init__(self, face, vert1, vert2, vert3, uvloop1, uvloop2, uvloop3):
        self.face = face
        self.vert1 = vert1
        self.vert2 = vert2
        self.vert3 = vert3
        self.loop1 = uvloop1
        self.loop2 = uvloop2
        self.loop3 = uvloop3

class UVUnwrappedChecker(Operator):
    """Check for unwrapped UVs that will cause tangent/binormal issues.\nThese are UVs from separate vertices that share the exact same UV coordinates for a face."""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "uvhelpers.unwrappedchecker"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Check for Unwrapped UVs"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')

    def uv_error(self, vert1, vert2, uv1, uv2):
        return vert1 != vert2 and uv1 == uv2

    def uv_checkforerrors(self, context, node):
        if node.type == "MESH":
            if (node.data is not None):

                #os.system("cls")

                mesh = node.data

                bm = bmesh.from_edit_mesh(mesh)
                bm.select_mode = {"VERT"}
                #bm.select_mode = {"VERT"}
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

    def uv_error_v2(self, uv1, uv2, uv3):
        s1 = float(uv2[0] - uv1[0]) # x
        s2 = float(uv3[0] - uv1[0])
        t1 = float(uv2[1] - uv1[1]) # y
        t2 = float(uv3[1] - uv1[1])
        
        check1 = float(s1 * t2 - s2 * t1)

        return abs(check1) < 0.00001

    def uv_checkforerrors_v2(self, context, node):
        if node.type == "MESH":
            if (node.data is not None):

                bpy.context.tool_settings.mesh_select_mode = (True, False, False)
                #py.context.tool_settings.mesh_select_mode = (False, False, True)

                mesh = node.data

                bm = bmesh.from_edit_mesh(mesh)
                bm.select_flush(False)
                uv_layer = bm.loops.layers.uv.active

                uv_errors = []

                for face in bm.faces:
                    if face in uv_errors:
                        continue

                    face.select = False
                    
                    if(len(face.loops) == 3):
                        vloop1 = face.loops[0]
                        vloop2 = face.loops[1]
                        vloop3 = face.loops[2]

                        vert1 = vloop1.vert
                        vert2 = vloop2.vert
                        vert3 = vloop3.vert

                        vert1.select_set(False)
                        vert2.select_set(False)
                        vert3.select_set(False)
                        
                        uvloop1 = vloop1[uv_layer]
                        uvloop2 = vloop2[uv_layer]
                        uvloop3 = vloop3[uv_layer]

                        uv1 = uvloop1.uv
                        uv2 = uvloop2.uv
                        uv3 = uvloop3.uv

                        #uv1 = vert1.co.xy
                        #uv2 = vert2.co.xy
                        #uv3 = vert3.co.xy

                        if self.uv_error_v2(uv1, uv2, uv3):
                            uv_error_entry = UVErrorv2(face, vert1, vert2, vert3, uvloop1, uvloop2, uvloop3)
                            uv_errors.append(uv_error_entry)
                        
                total_errors = len(uv_errors)
                if total_errors > 0:
                    for uv_error in uv_errors:
                        print("[ERROR]: UV problem detected!")
                        print("  Vert1: (%f,%f,%f)" % uv_error.vert1.co[:])
                        print("  Vert2: (%f,%f,%f)" % uv_error.vert2.co[:])
                        print("  Vert3: (%f,%f,%f)" % uv_error.vert3.co[:])
                        print("  UV1: (%f,%f)" % uv_error.loop1.uv[:])
                        print("  UV2: (%f,%f)" % uv_error.loop2.uv[:])
                        print("  UV3: (%f,%f)" % uv_error.loop3.uv[:])
                        uv_error.vert1.select_set(True)
                        uv_error.vert2.select_set(True)
                        uv_error.vert3.select_set(True)
                        uv_error.loop1.select = True
                        uv_error.loop2.select = True
                        uv_error.loop3.select = True

                    self.report({"WARNING"}, "[LL-UV-Helper] {} total problems found on UV map. Check selected vertices for wrapping issues.".format(total_errors))
                else:
                    self.report({"INFO"}, "[LL-UV-Helper] No UV problems found.")
                
                #total_errors.clear()

                bm.select_flush(True)
                bmesh.update_edit_mesh(mesh)

    def execute(self, context):        # execute() is called when running the operator.

        # The original script
        scene = context.scene

        if bpy.context.scene.objects.active is None:
            self.report({"WARNING"}, "[LL-UV-Helper] Select a mesh before checking UVs!")
            return {'FINISHED'}

        node = bpy.context.scene.objects.active

        bpy.ops.object.mode_set(mode="EDIT")
        self.uv_checkforerrors_v2(context, node)

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.


class UVHelperPanel(bpy.types.Panel):
    bl_label = "Helpers"
    bl_idname = "IMAGE_MT_ll_uvhelpers"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = 'Helpers'

    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    def draw(self, context):
        layout = self.layout
        layout.operator(UVUnwrappedChecker.bl_idname)

def register():
    #bpy.utils.register_module(__name__)
    return

def unregister():
    #bpy.utils.unregister_module(__name__)
    return

if __name__ == "__main__":
    register()