
import bpy

def get_preferences(context):
	if "laughingleader_blender_helpers" in context.user_preferences.addons:
		return context.user_preferences.addons["laughingleader_blender_helpers"].preferences
	return None

def safe_register(classes):
    for c in classes:
        try:
            print("[LeaderHelpers] Registering class {0}...".format(c))
            bpy.utils.register_class(c)
        except Exception as e:
            print("[LeaderHelpers] ERROR: Failed to register class {0}: {1}".format(c, e))

def safe_unregister(classes):
	for c in reversed(classes):
		try:
		    print("[LeaderHelpers] Unregistering class {0}...".format(c))
		    bpy.utils.unregister_class(c)
		except Exception as e:
		    print("[LeaderHelpers] ERROR: Failed to unregister class {0}: {1}".format(c, e))