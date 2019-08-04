LaughingLeader Helpers for Blender 2.79
=======

This is a set of helpers (packaged as one addon) that add additional functionality to Blender, all made with the intent to reduce tedious tasks.

_Note: This addon is currently experimental, so don't expect absolute stability!_

# Installing

## Manual Method  
* Download this repository as a zip (using the green Clone or download button).
* Save the addon somewhere where you can find it again.
* Extract the zip.
* Copy the folder `laughingleader_blender_helpers`. Make sure this is the folder with the scripts under it (`laughingleader_blender_helpers\__init__.py` etc).
* Paste the laughingleader_blender_helpers folder into your addons folder. Default:
```
C:\Users\Username\AppData\Roaming\Blender Foundation\Blender\2.79\scripts\addons\
```
* (Optional) Refer to Blender's guide for installing addons here: [Install from File](https://docs.blender.org/manual/en/latest/preferences/addons.html#header). It has a tip section for setting up a separate scripts/addons folder, outside of your appdata.

### Cloning  
* In Blender, navigate to File -> User Preferences -> File.
* The pathway for "Scripts" is where Blender will read new addon folders from. Add a pathway if it's blank.
* [Clone the repository](https://help.github.com/articles/cloning-a-repository/).
* Create a junction to the `laughingleader_blender_helpers` inside your scripts/addons folder.
  * You can create a junction with this command line command:
```
mklink /j "C:\Path1\laughingleader_blender_helpers" "C:\Path2\scripts\addons\laughingleader_blender_helpers"
```
| Rename | Description |
| --- | ----------- |
| Path1 | This should be the path where you cloned the repo. We want to junction the laughingleader_blender_helpers folder inside that contains all the py scripts.|
| Path2 | This is where your scripts/addons folder for Blender is. Either the AppData folder, or the custom scripts folder you set. We want to junction the laughingleader_blender_helpers folder with the py scripts to this folder. |
  * Alternatively, this program adds junction/symlink creating via right clicking files in a file explorer: [Link Shell Extension](http://schinagl.priv.at/nt/hardlinkshellext/linkshellextension.html#download)
    * With this program installed, right click the laughingleader_blender_helpers folder and select "Pick Link Source", then go to scripts/addons, right click the background, and select Drop As... -> Junction.

### Activating the Addon  
* In Blender, navigate to File -> User Preferences -> Add-ons
* Search for "Leader", or click Community -> System.
* Check the checkbox next to "LaughingLeader Helpers".

### Troubleshooting
* I don't see the addon inside Blender.  
  Make sure the folder with the scripts (laughingleader_blender_helpers/__init__.py, etc) is the folder inside scripts/addons. Blender won't read a nested folder. For example, if your folder is located like so: `scripts/addons/laughingleader_blender_helpers/laughingleader_blender_helpers`, Blender won't load the scripts or recognize the addon.

# Current Features:

## UV Helpers
Available in a new "Helpers" tab in the UV/Image Editor's Toolshelf.

### UV Errors
#### Check UV Triangles
Formats that utilize q-tangents (GR2 for one) have issues when UVs don't form a triangle. This helper identifies and selects those UVs for you.

### Misc
* Cursor to Last UV  
* Select Seams  
* Select Sharp Edges  
* Reload All Images  
* Delete Image Button  
If "Enable Delete Buttons" is enabled in the LaughingLeader Helpers User Preferences, you'll see a new delete button in the image editor window. This will allow you to delete an image without having to unlink it and restart Blender or purge unlinked data.

## Pose Helpers

### Pose Options -> Mirror X Axis
Mirrors location/rotation/scale on opposite bones along the x-axis. This helper looks for `L` or `R`, surrounded in underscores, depending on the selected bone. For instance, if your selected bone is `Dummy_L_Foot` or `Dummy_Foot_L`, then pose values will be mirrored on `DUmmy_R_Foot` or `Dummy_Foot_R`. 

## Animation Helpers

* Delete Action Button  
If "Enable Delete Buttons" is enabled in the LaughingLeader Helpers User Preferences, you'll see a new delete button in the Action Editor window. This will allow you to delete an action without having to unlink it and restart Blender or purge unlinked data.

## Object Helpers

### Mesh Data Tab
* Selection Groups  
Meshes now have a "Selection Groups" dropdown. This works like Vertex Groups, in that you can save selected vertices to a group, to allow you to select/deselect them with the provided buttons. The difference here is these groups are separate from vertex groups and don't alter bone deforms or weight painting, allowing you to keep your vertex groups clear of clutter.

## Export Helpers
Currently these helpers require an export addon to utilize them.

### Object Properties Panel
The following properties work best when the exporter creates copies of objects (such as the [DOS2DE Collada Exporter](https://github.com/LaughingLeader-DOS2-Mods/DOS2DE-Collada-Exporter) in recent versions). Currently, these don't do anything unless an exporter utilizes them.

#### Apply Transformations
Applies the selected transformations when exporting.
#### Export Name
The object takes on this name when exporting. Useful if you have multiple copies of the same object on various layers (possibly for different rigs), but want the exported mesh/etc name to be the same.

### Object Mode > Toolshelf > Export
#### Merging (WIP/Experimental)
Allows merging of objects when exporting. Useful for keeping your actual objects separate, for easier tweaking without needing to make continuous duplicates/backups.
