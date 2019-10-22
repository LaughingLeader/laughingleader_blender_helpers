from __future__ import division
import bpy
import bmesh
import math
import os.path
import os

from bpy.types import Operator, PropertyGroup, Panel
from bpy.props import CollectionProperty, PointerProperty, BoolProperty, FloatProperty, EnumProperty, StringProperty

from bl_ui import space_image

from . import leader

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

def error_missing_layer_names(self, context):
    self.layout.label("Layer Names are not enabled. Please enable the Layer Management or Leader Helpers addon for layer names.")

def error_no_active_object(self, context):
    self.layout.label("No active object set.")

class LLUVHelpers_TriangleError:
    def __init__(self, face, vert1, vert2, vert3, uvloop1, uvloop2, uvloop3):
        self.face = face
        self.vert1 = vert1
        self.vert2 = vert2
        self.vert3 = vert3
        self.loop1 = uvloop1
        self.loop2 = uvloop2
        self.loop3 = uvloop3

class LLUVHelpers_UnwrappedChecker(Operator):
    """Check for UVs that will cause tangent/binormal issues.\nThese are UV faces that fail to form a mathematical triangle"""
    bl_idname = "llhelpers.uv_unwrappedchecker"
    bl_label = "Check UV Triangles"
    bl_options = {'REGISTER', 'UNDO'}

    length_check_value = FloatProperty(default=0.0000001)

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')

    def uv_error(self, uv1, uv2, uv3):
        s1 = float(uv2[0] - uv1[0]) # x
        s2 = float(uv3[0] - uv1[0])
        t1 = float(uv2[1] - uv1[1]) # y
        t2 = float(uv3[1] - uv1[1])
        
        check1 = float(s1 * t2 - s2 * t1)

        is_error = abs(check1) < self.length_check_value

        if is_error:
            print("[LeaderHelpers] Found problematic UV triangle. Total: {0:.10f} < {1:.10f} Min".format(abs(check1), self.length_check_value))
            print("  UV1: x:{} y:{}".format(uv1[0], uv1[1]))
            print("  UV2: x:{} y:{}".format(uv2[0], uv2[1]))
            print("  UV3: x:{} y:{}".format(uv3[0], uv3[1]))

        return is_error

    def uv_checkforerrors(self, context, node):
        if node.type == "MESH":
            if (node.data is not None):

                preferences = leader.get_preferences(context)
                if preferences is not None:
                    select_mode = preferences.uvhelpers_errorchecker_select_mode
                else:
                    select_mode = "VERTEX"

                if select_mode == "FACE":
                    bpy.context.tool_settings.mesh_select_mode = (False, False, True)
                elif select_mode == "EDGE":
                    bpy.context.tool_settings.mesh_select_mode = (False, True, False)
                else:
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

                        if self.uv_error(uv1, uv2, uv3):
                            uv_error_entry = LLUVHelpers_TriangleError(face, vert1, vert2, vert3, uvloop1, uvloop2, uvloop3)
                            uv_errors.append(uv_error_entry)
                        
                total_errors = len(uv_errors)
                if total_errors > 0:
                    can_select = True
                    select_all = preferences is not None and preferences.uvhelpers_errorchecker_select_all is True
                    for uv_error in uv_errors:
                        print("[ERROR]: UV problem detected!")
                        print("  Vert1: (%f,%f,%f)" % uv_error.vert1.co[:])
                        print("  Vert2: (%f,%f,%f)" % uv_error.vert2.co[:])
                        print("  Vert3: (%f,%f,%f)" % uv_error.vert3.co[:])
                        print("  UV1: (%f,%f)" % uv_error.loop1.uv[:])
                        print("  UV2: (%f,%f)" % uv_error.loop2.uv[:])
                        print("  UV3: (%f,%f)" % uv_error.loop3.uv[:])

                        if can_select:
                            uv_error.vert1.select_set(True)
                            uv_error.vert2.select_set(True)
                            uv_error.vert3.select_set(True)
                            uv_error.loop1.select = True
                            uv_error.loop2.select = True
                            uv_error.loop3.select = True
                            if select_all == False:
                                can_select = False
                                break

                    self.report({"WARNING"}, "[LL-UV-Helper] {} total problems found on UV map. Check selected vertices for wrapping issues.".format(total_errors))
                else:
                    self.report({"INFO"}, "[LL-UV-Helper] No UV problems found.")
                
                #total_errors.clear()

                bm.select_flush(True)
                bmesh.update_edit_mesh(mesh)

    def execute(self, context):
        scene = context.scene

        if bpy.context.scene.objects.active is None:
            self.report({"WARNING"}, "[LL-UV-Helper] Select a mesh before checking UVs!")
            return {'FINISHED'}

        node = bpy.context.scene.objects.active

        bpy.ops.object.mode_set(mode="EDIT")
        self.uv_checkforerrors(context, node)

        return {'FINISHED'}

def selectedUVs(mesh, bmesh=None, uvlayer=None, sync=False):
    '''Get the vertices visible and selected in the UV view.'''
    uvs = {}
    if bmesh is None:
        uvlayer = uvlayer or mesh.uv_layers.active
        for f, uv in zip(mesh.loops, uvlayer.data):
            #print("UVLayer: {} | f: {} uv: {}".format(uvlayer.name, f, uv))
            if mesh.vertices[f.vertex_index].select and (sync or uv.select):
                uvs[f.vertex_index] = uv.uv
                #uvs.append(uv.uv)
    else:
        uv_layer = uvlayer or bmesh.loops.layers.uv.active

        for face in bmesh.faces:
            for loop in face.loops:
                luv = loop[uv_layer]
                if (luv.select or sync) and loop.vert.select:
                    print(loop.index)
                    uvs[loop.index] = luv
                    #uvs.append(luv)
    return uvs

last_selected_uvs = []
last_selection = None

class LLUVHelpers_SelectCursorOperator(Operator):
    """Move the cursor to the last selected UV"""      # Use this as a tooltip for menu items and buttons.
    bl_idname = "llhelpers.uv_3dcursortolastuv"        # Unique identifier for buttons and menu items to reference.
    bl_label = "Cursor to Last UV"         # Display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # Enable undo for the operator.

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')

    def execute(self, context):        # execute() is called when running the operator.

        print("Looking for selected UVs...")

        node = bpy.context.scene.objects.active

        if node.type == "MESH":
            if (node.data is not None):

                mesh = node.data
                bm = bmesh.from_edit_mesh(mesh)

                selected = selectedUVs(mesh=mesh, bmesh=bm, sync=context.scene.tool_settings.use_uv_select_sync)
                total = len(selected)
                if len(selected) > 0:

                    global last_selected_uvs
                    global last_selection

                    selection = 0
                    for key in selected.keys():
                        selection += key
                    
                    if selection == last_selection:
                        last_total = len(last_selected_uvs)
                        if last_total == total:
                            last = last_selected_uvs[-1]
                            last_selected_uvs.clear()
                            last_selected_uvs.append(last)
                    else:
                        last_selected_uvs.clear()

                    for i, uvdata in selected.items():
                        if not i in last_selected_uvs:
                            bpy.ops.uv.cursor_set(location=uvdata.uv)
                            last_selected_uvs.append(i)
                            break

                    last_selection = selection
                
                # uv_layer = bm.loops.layers.uv.active
                # for f in bm.faces:
                #     for l in f.loops:
                #         luv = l[uv_layer]
                #         if luv.select:
                #             bpy.ops.uv.cursor_set(location=luv.uv)
                #             print(luv.uv)
                #             break

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.

class LLUVHelpers_SelectSharpOperator(Operator):
    """Selects all seams"""
    bl_idname = "llhelpers.uv_sharpselecter"
    bl_label = "Select Sharps Edges"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')

    def execute(self, context):
        scene = context.scene

        if context.object is None:
            self.report({"WARNING"}, "[LL-UV-Helper] No object selected!")
            return {'FINISHED'}

        node = bpy.context.scene.objects.active

        bpy.ops.object.mode_set(mode="EDIT")
        if node.type == "MESH":
            if (node.data is not None):
                mesh = node.data

                bm = bmesh.from_edit_mesh(mesh)
                for edge in bm.edges:
                    if edge.smooth == False:
                        if bm.select_mode == "VERT":
                            for v in edge.verts:
                                v.select = True
                        else:
                            edge.select = True
                bmesh.update_edit_mesh(mesh)

        return {'FINISHED'}

class LLUVHelpers_SelectSeamOperator(Operator):
    """Selects all seams"""
    bl_idname = "llhelpers.uv_seamselecter"
    bl_label = "Select Seams"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.mode == 'EDIT_MESH')

    def execute(self, context):
        scene = context.scene

        if bpy.context.scene.objects.active is None:
            self.report({"WARNING"}, "[LL-UV-Helper] Select a mesh before selecting seams!")
            return {'FINISHED'}

        node = bpy.context.scene.objects.active

        bpy.ops.object.mode_set(mode="EDIT")
        if node.type == "MESH":
            if (node.data is not None):
                mesh = node.data

                bm = bmesh.from_edit_mesh(mesh)
                for edge in bm.edges:
                    #edge.select_set(False)
                    if edge.seam:
                        if bm.select_mode == "VERT":
                            for v in edge.verts:
                                v.select = True
                        else:
                            edge.select = True

                #bm.select_flush(False)
                bmesh.update_edit_mesh(mesh)

        return {'FINISHED'}

class LEADER_PT_imageeditor_tools_uv_helpers(Panel):
    bl_label = "UV Helpers"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = 'Helpers'

    expand_uv_errors = BoolProperty(
        options={"HIDDEN"},
        default=True
    )

    expand_image_helpers = BoolProperty(
        options={"HIDDEN"},
        default=False
    )

    @classmethod
    def poll(cls, context):
        return (context.object is not None)

    def draw(self, context):
        layout = self.layout
        layout.label("UV Errors")
        box = layout.box()
        #layout.prop(self, "select_all")
        preferences = leader.get_preferences(context)
        length_check_value = 10 #0.00000010
        if preferences is not None:
            length_check_value = float(preferences.uvhelpers_errorchecker_length_check_value/100000000)
            box.prop(preferences, "uvhelpers_errorchecker_length_check_value")
            length_check_value_str = "Min Length: "+'{0:.8f}'.format(length_check_value)
            box.label(length_check_value_str)
            box.prop(preferences, "uvhelpers_errorchecker_select_all")
            box.prop(preferences, "uvhelpers_errorchecker_select_mode")
        uv_helper_op = box.operator(LLUVHelpers_UnwrappedChecker.bl_idname)
        uv_helper_op.length_check_value = length_check_value

        layout.label("Misc")
        layout.operator(LLUVHelpers_SelectCursorOperator.bl_idname)
        layout.operator(LLUVHelpers_SelectSeamOperator.bl_idname)
        layout.operator(LLUVHelpers_SelectSharpOperator.bl_idname)

class LLUVHelpers_DeleteOperator(Operator):
    """Delete this image data"""
    bl_label = "Delete Image"
    bl_idname = "llhelpers.uv_imagedelete"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.space_data.image != None

    def execute(self, context):
        ob = bpy.context.object
        image_name = (context.space_data.image.name
            if context.space_data.image is not None
            else "")

        msg = ""
        msg_type = "INFO"

        if image_name != "":
            try:
                index = bpy.data.images.find(image_name)
                if index > -1:
                    image = bpy.data.images[index]
                    bpy.data.images.remove(image)
                    msg = "[LeaderHelpers:UVHelpers:Delete] Deleted image '{}'. Undo to reverse.".format(image_name)
                    context.scene.update()
            except Exception as e:
                msg = "[LeaderHelpers:UVHelpers:Delete] Error deleting image:\n\t{}".format(e)
                msg_type = "ERROR"
        else:
            msg = "[LeaderHelpers:UVHelpers:Delete] Failed to find the current image."
            msg_type = "WARNING"

        if msg != "":
            self.report({msg_type}, msg)
        return {'FINISHED'}

    def invoke(self, context, _event):
        return self.execute(context)
class LLUVHelpers_ImageReloaderOperator(Operator):
    """Reloads all images from their source"""
    bl_idname = "llhelpers.uv_reloadimages"
    bl_label = "Reload All Images"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        updated_image = False
        for image in context.blend_data.images:
            if image.filepath != "":
                path_check = bpy.path.abspath(image.filepath, library=image.library)
                if os.path.exists(path_check):
                    image.reload()
                    print("[LL-UV-Helper] Reloaded image: \"{}\"".format(path_check))
                    updated_image = True
                else:
                    print("[LL-UV-Helper] Skipped reloading image (file does not exist): \"{}\"".format(path_check))

        if updated_image:
            for area in bpy.context.screen.areas:
                if area.type in ['IMAGE_EDITOR']:
                    area.tag_redraw()

        return {'FINISHED'}            # Lets Blender know the operator finished successfully.


class LEADER_OT_image_helpers_quickexport(Operator):
    """Exports the current image quickly"""
    bl_idname = "llhelpers.image_quickexportoperator"
    bl_label = "Quick Export Image"
    bl_options = {'REGISTER'}

    filepath = StringProperty(
        default=""
    )

    @classmethod
    def poll(cls, context):
        return context.space_data.image != None

    def execute(self, context):
        if self.filepath != "":
            try:
                bpy.ops.image.save_as(filepath=self.filepath)
                self.report({"INFO"}, "[LeaderHelpers:ExportImage] Saved image to '{}'".format(self.filepath))
            except Exception as e:
                self.report({"ERROR"}, "[LL-UV-Helper:ExportImage] Error occured when exporting image.")
                print("[LL-UV-Helper:ExportImage] Error occured when exporting image: {}.".format(e))
            return {'FINISHED'}
        else:
            self.report({"WARNING"}, "[LL-UV-Helper:ExportImage] File path not set. Skipping")
            return {'CANCELLED'}

class LEADER_PT_imageeditor_tools_image_helpers(Panel):
    bl_label = "Image Helpers"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = 'Helpers'

    @classmethod
    def poll(cls, context):
        return context.space_data.image != None

    def draw(self, context):
        preferences = leader.get_preferences(context)
        layout = self.layout

        layout.operator(LLUVHelpers_ImageReloaderOperator.bl_idname)

        layout.label("Export", icon="FILE_IMAGE")
        box = layout.box()
        if preferences is not None:
            box.prop(preferences, "uvhelpers_images_quickexport_autoname")
            box.prop(preferences, "uvhelpers_images_quickexport_manualname")
            box.prop(preferences, "uvhelpers_images_quickexport_append")
            box.label("Export To:", icon="EXPORT")
            box.prop(preferences, "uvhelpers_images_quickexport_filepath", text="")
            export_path = bpy.path.basename(preferences.uvhelpers_images_quickexport_filepath)
            box.label(export_path)
            op = box.operator(LEADER_OT_image_helpers_quickexport.bl_idname)
            op.filepath = preferences.uvhelpers_images_quickexport_filepath

# Draw Overrides

def IMAGE_HT_header_draw(self, context):
    layout = self.layout

    sima = context.space_data
    ima = sima.image
    iuser = sima.image_user
    toolsettings = context.tool_settings
    mode = sima.mode

    show_render = sima.show_render
    show_uvedit = sima.show_uvedit
    show_maskedit = sima.show_maskedit

    row = layout.row(align=True)
    row.template_header()

    space_image.MASK_MT_editor_menus.draw_collapsible(context, layout)

    layout.template_ID(sima, "image", new="image.new", open="image.open")
    if not show_render:
        layout.prop(sima, "use_image_pin", text="")

    preferences = leader.get_preferences(context)
    if preferences is not None and preferences.general_enable_deletion:
        layout.operator(LLUVHelpers_DeleteOperator.bl_idname, icon="CANCEL", text="", emboss=False)

    layout.prop(sima, "mode", text="")

    if show_maskedit:
        row = layout.row()
        row.template_ID(sima, "mask", new="mask.new")

    layout.prop(sima, "pivot_point", icon_only=True)

    # uv editing
    if show_uvedit:
        uvedit = sima.uv_editor
        layout.prop(toolsettings, "use_uv_select_sync", text="")

        if toolsettings.use_uv_select_sync:
            layout.template_edit_mode_selection()
        else:
            layout.prop(toolsettings, "uv_select_mode", text="", expand=True)
            layout.prop(uvedit, "sticky_select_mode", icon_only=True)

        row = layout.row(align=True)
        row.prop(toolsettings, "proportional_edit", icon_only=True)
        if toolsettings.proportional_edit != 'DISABLED':
            row.prop(toolsettings, "proportional_edit_falloff", icon_only=True)

        row = layout.row(align=True)
        row.prop(toolsettings, "use_snap", text="")
        row.prop(toolsettings, "snap_uv_element", icon_only=True)
        if toolsettings.snap_uv_element != 'INCREMENT':
            row.prop(toolsettings, "snap_target", text="")

        mesh = context.edit_object.data
        layout.prop_search(mesh.uv_textures, "active", mesh, "uv_textures", text="")

    if ima:
        if ima.is_stereo_3d:
            row = layout.row()
            row.prop(sima, "show_stereo_3d", text="")

        # layers
        layout.template_image_layers(ima, iuser)

        # draw options
        row = layout.row(align=True)
        row.prop(sima, "draw_channels", text="", expand=True)

        row = layout.row(align=True)
        if ima.type == 'COMPOSITE':
            row.operator("image.record_composite", icon='REC')
        if ima.type == 'COMPOSITE' and ima.source in {'MOVIE', 'SEQUENCE'}:
            row.operator("image.play_composite", icon='PLAY')

    if show_uvedit or show_maskedit or mode == 'PAINT':
        layout.prop(sima, "use_realtime_update", icon_only=True, icon='LOCKED')

def draw_snap_addon(self, context):
    self.layout.operator(LLUVHelpers_SelectCursorOperator.bl_idname, icon="PLUGIN")

DOPESHEET_HT_header_draw_original = None

def register():
    global DOPESHEET_HT_header_draw_original
    DOPESHEET_HT_header_draw_original = bpy.types.IMAGE_HT_header.draw
    bpy.types.IMAGE_HT_header.draw = IMAGE_HT_header_draw

    bpy.types.IMAGE_MT_uvs_snap.append(draw_snap_addon)
    return

def unregister():
    try:
        global DOPESHEET_HT_header_draw_original
        if DOPESHEET_HT_header_draw_original is not None:
            bpy.types.IMAGE_HT_header.draw = DOPESHEET_HT_header_draw_original
            DOPESHEET_HT_header_draw_original = None

        bpy.types.IMAGE_MT_uvs_snap.remove(draw_snap_addon)
    except: pass
    return

if __name__ == "__main__":
    register()