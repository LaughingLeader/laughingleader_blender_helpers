import bpy
from . import UV_Helpers

bl_info = {
    "name": "LaughingLeader Helpers",
    "author": "LaughingLeader",
    "blender": (2, 7, 9),
    "api": 38691,
    "location": "",
    "description": (""),
    "warning": "",
    "wiki_url": (""),
    "tracker_url": "",
    "support": "COMMUNITY",
    "category": "System"}

def register():
    #bpy.utils.register_module(__name__)
    UV_Helpers.register()

def unregister():
    #bpy.utils.unregister_module(__name__)
    UV_Helpers.unregister()

if __name__ == "__main__":
    register()