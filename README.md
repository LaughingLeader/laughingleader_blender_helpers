LaughingLeader Blender Helpers
=======

This is a set of helpers (packaged as one addon) that add additional functionality to Blender, all made with the intent to reduce tedious tasks.

_Note: This addon is currently experimental, so don't expect absolute stability!_

# Current Features:
## Export Helpers
Currently these helpers require an export addon to utilize them.

### Object Properties Panel
The following properties work best when the exporter creates copies of objects (such as the [DOS2DE Collada Exporter](https://github.com/LaughingLeader-DOS2-Mods/DOS2DE-Collada-Exporter) in recent versions). Currently, these don't do anything unless an exporter utilizes them.

#### Apply Transformations
Applies the selected transformations when exporting.
#### Export Name
The object takes on this name when exporting. Useful if you have multiple copies of the same object on various layers (possibly for different rigs), but want the exported mesh/etc name to be the same.

### Object Mode > Toolshelf > Export
#### Merging (WIP)
Allows merging of objects when exporting. Useful for keeping your actual objects separate, for easier tweaking without needing to make continuous duplicates/backups.

## UV Helpers
#### Check for unwrapped vertices
Formats that utilize q-tangents (gr2 for one) have issues when UVs don't form a triangle. This helper identifies and highlights those UVs for you.
