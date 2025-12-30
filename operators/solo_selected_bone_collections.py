# pyright: reportInvalidTypeForm=false
import bpy
from bpy.types import Operator
from bpy.props import BoolProperty

from ..keymap_manager import KeymapDefinition, keymap_registry
from ..utils.logging import get_logger

log = get_logger(__name__)


def _get_selected_pose_bones(context):
    pbs = list(getattr(context, "selected_pose_bones", []) or [])
    if not pbs and getattr(context, "active_pose_bone", None):
        pbs = [context.active_pose_bone]
    return pbs


def _collections_for_bones(arm_data, bones):
    # Robust approach: iterate armature collections and test membership via BoneCollection.bones.
    # (Avoid relying on a hypothetical bone.collections property across versions.)
    targets = set()
    for bc in arm_data.collections:
        # Optional: ignore technical collections by name prefix if you want:
        # if bc.name.startswith(("MCH", "ORG", "DEF")):
        #     continue
        bset = bc.bones  # read-only collection of Bones
        for b in bones:
            # bpy_prop_collection expects string (bone name) for __contains__
            if b.name in bset:
                targets.add(bc)
    return targets


def _supports_is_solo(arm_data):
    try:
        for bc in arm_data.collections:
            return hasattr(bc, "is_solo")
    except Exception:
        pass
    return False


class POSE_OT_solo_selected_bone_collections(Operator):
    bl_idname = "pose.solo_selected_bone_collections"
    bl_label = "Solo Selected Bone Collections"
    bl_description = (
        "Solo (star) the Bone Collection(s) that contain the selected bone(s)"
    )
    bl_options = {"REGISTER", "UNDO"}

    add_to_existing: BoolProperty(
        name="Add to Existing Solo",
        description="Keep existing solo collections and add these; otherwise replace",
        default=False,
    )

    toggle_if_same: BoolProperty(
        name="Toggle Off If Same",
        description="If the same collections are already solo, clear solo instead",
        default=True,
    )

    ensure_visible: BoolProperty(
        name="Ensure Visible",
        description="Force targeted collections to be visible (is_visible = True)",
        default=True,
    )

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return ob and ob.type == "ARMATURE" and context.mode == "POSE"

    def execute(self, context):
        ob = context.active_object
        arm = ob.data

        pbs = _get_selected_pose_bones(context)
        if not pbs:
            self.report(
                {"WARNING"}, "No pose bones selected (and no active pose bone)."
            )
            return {"CANCELLED"}

        bones = [pb.bone for pb in pbs if getattr(pb, "bone", None)]
        if not bones:
            self.report({"WARNING"}, "Selection has no valid bones.")
            return {"CANCELLED"}

        targets = _collections_for_bones(arm, bones)
        if not targets:
            self.report(
                {"WARNING"}, "Selected bones are not assigned to any Bone Collection."
            )
            return {"CANCELLED"}

        if not _supports_is_solo(arm):
            self.report(
                {"ERROR"},
                "This Blender build does not expose BoneCollection.is_solo in Python.",
            )
            return {"CANCELLED"}

        current_solo = {bc for bc in arm.collections if getattr(bc, "is_solo", False)}

        if self.toggle_if_same and current_solo == targets:
            for bc in arm.collections:
                bc.is_solo = False
            return {"FINISHED"}

        if not self.add_to_existing:
            for bc in arm.collections:
                bc.is_solo = False

        for bc in targets:
            bc.is_solo = True
            if self.ensure_visible and hasattr(bc, "is_visible"):
                bc.is_visible = True

        return {"FINISHED"}


class POSE_OT_clear_bone_collection_solo(Operator):
    bl_idname = "pose.clear_bone_collection_solo"
    bl_label = "Clear Bone Collection Solo"
    bl_description = "Clear (unset) solo on all Bone Collections"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return (
            ob
            and ob.type == "ARMATURE"
            and context.mode in {"POSE", "OBJECT", "EDIT_ARMATURE"}
        )

    def execute(self, context):
        ob = context.active_object
        arm = ob.data
        if not _supports_is_solo(arm):
            self.report(
                {"ERROR"},
                "This Blender build does not expose BoneCollection.is_solo in Python.",
            )
            return {"CANCELLED"}
        for bc in arm.collections:
            bc.is_solo = False
        return {"FINISHED"}


# -----------------------------------------------------------------------------
# Keymap Registration
# -----------------------------------------------------------------------------
keymap_registry.register_keymap_group(
    "Solo Bone Collections",
    [
        KeymapDefinition(
            operator_id="pose.solo_selected_bone_collections",
            key="SLASH",
            name="Pose",
            space_type="EMPTY",
            description="Solo the Bone Collection(s) containing selected bones",
        ),
        KeymapDefinition(
            operator_id="pose.clear_bone_collection_solo",
            key="SLASH",
            alt=1,
            name="Pose",
            space_type="EMPTY",
            description="Clear solo on all Bone Collections",
        ),
    ],
)
