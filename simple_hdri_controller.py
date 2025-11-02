bl_info = {
    "name": "Simple HDRI Controller",
    "author": "ChatGPT",
    "version": (1, 0, 1),
    "blender": (3, 0, 0),
    "location": "3D Viewport > N-panel > HDRI",
    "description": "Load an HDRI and rotate it from a simple panel. Drag & drop supported.",
    "category": "3D View",
}

import bpy
from bpy.props import PointerProperty, FloatProperty, StringProperty
from bpy.types import Operator, Panel, PropertyGroup
from math import radians

# ---------- Safe context helpers ----------

def _safe_scene(ctx=None):
    """Return a usable Scene or None without assuming ctx.scene exists."""
    ctx = ctx or bpy.context
    if hasattr(ctx, "scene") and ctx.scene:
        return ctx.scene
    # Fallbacks for restricted contexts (e.g. prefs register/import)
    if bpy.context and getattr(bpy.context, "scene", None):
        return bpy.context.scene
    if bpy.data.scenes:
        return bpy.data.scenes[0]
    return None

# ---------- Node setup helpers ----------

def ensure_world_node_setup(ctx=None):
    """Ensure the World has: TexCoord -> Mapping -> EnvTex -> Background -> World Output."""
    scene = _safe_scene(ctx)
    if not scene:
        return None  # No scene yet (e.g. during add-on enable in prefs)
    world = scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        scene.world = world

    world.use_nodes = True
    nt = world.node_tree
    nodes = nt.nodes
    links = nt.links

    out = nodes.get("World Output")
    if not out or out.type != 'OUTPUT_WORLD':
        out = nodes.new("ShaderNodeOutputWorld")
        out.name = "World Output"
        out.location = (600, 0)

    bg = nodes.get("HDRI Background")
    if not bg or bg.type != 'BACKGROUND':
        bg = nodes.new("ShaderNodeBackground")
        bg.name = "HDRI Background"
        bg.location = (400, 0)

    env = nodes.get("HDRI Environment")
    if not env or env.type != 'TEX_ENVIRONMENT':
        env = nodes.new("ShaderNodeTexEnvironment")
        env.name = "HDRI Environment"
        env.location = (200, 0)

    mapping = nodes.get("HDRI Mapping")
    if not mapping or mapping.type != 'MAPPING':
        mapping = nodes.new("ShaderNodeMapping")
        mapping.name = "HDRI Mapping"
        mapping.location = (0, 0)

    texcoord = nodes.get("HDRI TexCoord")
    if not texcoord or texcoord.type != 'TEX_COORD':
        texcoord = nodes.new("ShaderNodeTexCoord")
        texcoord.name = "HDRI TexCoord"
        texcoord.location = (-200, 0)

    def link_once(from_socket, to_socket):
        if not from_socket or not to_socket:
            return
        for l in to_socket.links:
            if l.from_socket == from_socket:
                return
        links.new(from_socket, to_socket)

    link_once(texcoord.outputs.get("Generated"), mapping.inputs.get("Vector"))
    link_once(mapping.outputs.get("Vector"), env.inputs.get("Vector"))
    link_once(env.outputs.get("Color"), bg.inputs.get("Color"))
    link_once(bg.outputs.get("Background"), out.inputs.get("Surface"))

    return {
        "world": world,
        "out": out,
        "bg": bg,
        "env": env,
        "mapping": mapping,
        "texcoord": texcoord,
    }

def apply_hdri_image(ctx, image):
    nodes = ensure_world_node_setup(ctx)
    if not nodes:
        return
    env = nodes["env"]
    env.image = image if image and image.type == 'IMAGE' else None

def set_hdri_rotation_deg(ctx, degrees):
    nodes = ensure_world_node_setup(ctx)
    if not nodes:
        return
    mapping = nodes["mapping"]
    rot = list(mapping.inputs["Rotation"].default_value)
    rot[2] = radians(degrees)
    mapping.inputs["Rotation"].default_value = rot

def set_hdri_strength(ctx, strength):
    nodes = ensure_world_node_setup(ctx)
    if not nodes:
        return
    bg = nodes["bg"]
    bg.inputs["Strength"].default_value = strength

# ---------- Properties & their updates ----------

def _update_image(self, context):
    apply_hdri_image(context, self.image)

def _update_rotation(self, context):
    set_hdri_rotation_deg(context, self.rotation_deg)

def _update_strength(self, context):
    set_hdri_strength(context, self.strength)

class SHDRI_Props(PropertyGroup):
    image: PointerProperty(
        name="HDRI",
        description="HDRI image (.hdr/.exr). Drag & drop here or use Load.",
        type=bpy.types.Image,
        update=_update_image,
    )
    rotation_deg: FloatProperty(
        name="Rotation",
        description="Rotate the HDRI around Z (degrees)",
        subtype='ANGLE',
        default=0.0,
        soft_min=-360.0, soft_max=360.0,
        update=_update_rotation,
    )
    strength: FloatProperty(
        name="Strength",
        description="Background light intensity",
        default=1.0,
        min=0.0, soft_max=10.0,
        update=_update_strength,
    )

# ---------- Operators ----------

class SHDRI_OT_load_hdri(Operator):
    """Load an HDRI and wire it to the World nodes"""
    bl_idname = "shdri.load_hdri"
    bl_label = "Load HDRI"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default="*.hdr;*.exr;*.HDR;*.EXR", options={'HIDDEN'})
    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        if not self.filepath:
            self.report({'WARNING'}, "No file selected")
            return {'CANCELLED'}

        # Reuse if already loaded
        abspath = bpy.path.abspath(self.filepath)
        img = next((i for i in bpy.data.images if bpy.path.abspath(i.filepath) == abspath), None)
        if not img:
            try:
                img = bpy.data.images.load(self.filepath)
            except Exception as e:
                self.report({'ERROR'}, f"Failed to load image: {e}")
                return {'CANCELLED'}

        props = _safe_scene(context).shdri_props if _safe_scene(context) else None
        if props:
            props.image = img  # triggers update
        else:
            # Last resort: apply directly
            apply_hdri_image(context, img)

        self.report({'INFO'}, f"HDRI loaded: {img.name}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class SHDRI_OT_reset(Operator):
    """Reset rotation and strength"""
    bl_idname = "shdri.reset"
    bl_label = "Reset HDRI Settings"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = _safe_scene(context)
        if not scene:
            return {'CANCELLED'}
        props = scene.shdri_props
        props.rotation_deg = 0.0
        props.strength = 1.0
        self.report({'INFO'}, "HDRI settings reset")
        return {'FINISHED'}

# ---------- UI Panel ----------

class SHDRI_PT_panel(Panel):
    bl_label = "Simple HDRI"
    bl_idname = "SHDRI_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "HDRI"

    def draw(self, context):
        layout = self.layout
        scene = _safe_scene(context)
        if not scene:
            layout.label(text="No active scene.", icon='ERROR')
            return
        props = scene.shdri_props

        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator("shdri.load_hdri", icon='FILE_FOLDER', text="Load HDRI")
        col.separator()
        col.template_ID(props, "image", open="shdri.load_hdri")
        col.separator()
        col.prop(props, "rotation_deg", text="Rotation (°)")
        col.prop(props, "strength", text="Strength")
        col.separator()
        col.operator("shdri.reset", icon='LOOP_BACK')

# ---------- Registration ----------

classes = (
    SHDRI_Props,
    SHDRI_OT_load_hdri,
    SHDRI_OT_reset,
    SHDRI_PT_panel,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.shdri_props = PointerProperty(type=SHDRI_Props)
    # IMPORTANT: do NOT touch context/scene/world here; restricted contexts lack .scene

def unregister():
    del bpy.types.Scene.shdri_props
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
