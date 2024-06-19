import bpy
import bmesh
import re
from mathutils import Vector

bl_info = {
    "name" : "Split_Mesh_Helper",
    "author" : "dddder4",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "category" : "Mesh"
}

items = [
    ("0", '-X to X', '', '', 1),
    ("1", '-Y to Y', '', '', 2),
    ("2", '-Z to Z', '', '', 3),
]

def duplicate():
    bpy.ops.object.duplicate_move(OBJECT_OT_duplicate={"linked":False, "mode":'TRANSLATION'}, TRANSFORM_OT_translate={"value":(0, 0, 0), "orient_axis_ortho":'X', "orient_type":'GLOBAL', "orient_matrix":((0, 0, 0), (0, 0, 0), (0, 0, 0)), "orient_matrix_type":'GLOBAL', "constraint_axis":(False, False, False), "mirror":False, "use_proportional_edit":False, "proportional_edit_falloff":'SMOOTH', "proportional_size":1, "use_proportional_connected":False, "use_proportional_projected":False, "snap":False, "snap_elements":{'INCREMENT'}, "use_snap_project":False, "snap_target":'CLOSEST', "use_snap_self":True, "use_snap_edit":True, "use_snap_nonedit":True, "use_snap_selectable":False, "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "gpencil_strokes":False, "cursor_transform":False, "texture_space":False, "remove_on_cancel":False, "view2d_edge_pan":False, "release_confirm":False, "use_accurate":False, "use_automerge_and_split":False})
    
def move_to_collection(context, collectionName):
    if bpy.data.collections.get(collectionName,None) == None:#Create collection if the name given doesn't exist
        newCollection = bpy.data.collections.new(collectionName)
        context.scene.collection.children.link(newCollection)
    layer_collection = bpy.data.collections[collectionName]
    for obj in context.selected_objects:
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        layer_collection.objects.link(obj) #link it with collection

def rename(minVector, maxVector, objs):
    vectorDis = maxVector - minVector
    pr = prefs()
    order = int(pr.order)
    reverse = pr.reverse
    space = [0, 1, 2]
    division1 = pr.division1 + 1
    division2 = pr.division2 + 1
    group_start = pr.group_start
    mat_index = pr.mat_index
    mat_name = pr.mat_name
    space.remove(order)
    bb_divide = [[[] for j in range(division2)] for i in range(division1)]

    for obj in objs:
        local_bbox_center = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
        global_bbox_center = obj.matrix_world @ local_bbox_center
        obj['global_bbox_center'] = global_bbox_center
        bb_divide_index1 = int((global_bbox_center[space[0]] - minVector[space[0]]) * division1 / vectorDis[space[0]])
        if global_bbox_center[space[0]] == maxVector[space[0]]:
            bb_divide_index1 -= 1
        bb_divide_index2 = int((global_bbox_center[space[1]] - minVector[space[1]]) * division2 / vectorDis[space[1]])
        if global_bbox_center[space[1]] == maxVector[space[1]]:
            bb_divide_index2 -= 1
        bb_divide[bb_divide_index1][bb_divide_index2].append(obj)
        
    # print("[")
    res_str2 = "[\n"
    for i in bb_divide:
        for j in i:
            if len(j) == 0:
                continue
            k = sorted(j, key = lambda x : x['global_bbox_center'][order], reverse = reverse)
            res_str = "["
            for sort_obj in k:
                name = "LOD_1_Group_" + str(group_start) + "_Sub_" + str(mat_index) + "__" + mat_name
                if bpy.data.objects.find(name) != -1:
                    bpy.data.objects[name].name = name + ".001"
                sort_obj.name = name
                res_str = res_str + str(group_start) + ", "
                group_start += 1
            res_str = res_str[:-2] + "],\n"
            # if j != i[-1]:
            #     res_str = res_str + ","
            # print(res_str)
            res_str2 = res_str2 + res_str
    # print("]")
    res_str2 = res_str2[:-2] + "\n]"
    print("---------------------------------")
    print(res_str2)
    print("---------------------------------")

def prefs():
    return bpy.context.preferences.addons[__name__].preferences

class ToolPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    max_group: bpy.props.IntProperty(name="Max Group", default=255)
    expect_group: bpy.props.IntProperty(name="Expect Groups", default=100)
    order: bpy.props.EnumProperty(name="Order Direction", items=items)
    reverse: bpy.props.BoolProperty(name="Reverse Direction", default=False)
    division1: bpy.props.IntProperty(name="Value", default=0)
    division2: bpy.props.IntProperty(name="Value", default=0)
    group_start: bpy.props.IntProperty(name="Group Start", default=1)
    mat_index: bpy.props.IntProperty(name="Material Index", default=1)
    mat_name: bpy.props.StringProperty(name="Material Name", default="none")

class SplitPreview(bpy.types.Operator):
    bl_idname = "splitmeshhelper.preview"
    bl_label = "Split Preview"
    # bl_description = "Description that shows in blender tooltips"
    bl_options = {"REGISTER"}

    first_click: bpy.props.BoolProperty(name="First Click", default=True)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        pr = prefs()
        # obj = context.object
        if self.first_click == True:
            bpy.ops.wm.console_toggle()
            self.first_click = False
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.mark_seam(clear=True)
        bpy.ops.mesh.select_all(action='DESELECT')

        # 获取当前编辑模式下的网格数据
        obj = context.active_object
        me = obj.data
        # 创建一个bmesh实例并加载网格数据
        bm = bmesh.from_edit_mesh(me)

        group_count = 0

        bm.faces.ensure_lookup_table()
        face_num = len(bm.faces)
        face_threshold = face_num / pr.expect_group
        for i in range(face_num):
            face = bm.faces[i]
            if face.hide == False:
                face.select_set(True)
                # bpy.ops.mesh.select_more()
                face_sel = me.total_face_sel
                while face_sel < face_threshold:
                    bpy.ops.mesh.select_more()
                    if face_sel == me.total_face_sel:
                        break
                    else:
                        face_sel = me.total_face_sel
                bpy.ops.mesh.region_to_loop()
                bpy.ops.mesh.mark_seam(clear=False)
                group_count += 1
                bpy.ops.mesh.loop_to_region()
                bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
                bpy.ops.mesh.hide(unselected=False)
                print(str(i) + " / " + str(face_num) + ", group: " + str(group_count))
                if group_count > pr.max_group:
                    bpy.ops.mesh.reveal()
                    bpy.ops.mesh.select_all(action='SELECT')
                    bpy.ops.mesh.mark_seam(clear=True)
                    break;
        print("FINISHED")
        bpy.ops.mesh.reveal()
        return {"FINISHED"}

class SplitConfirm(bpy.types.Operator):
    bl_idname = "splitmeshhelper.confirm"
    bl_label = "Split Confirm"
    bl_description = ""
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        pr = prefs()

        bpy.ops.object.mode_set(mode='OBJECT')

        bound_box = [context.object.matrix_world @ Vector(b) for b in context.object.bound_box]
        bound_box = sorted(bound_box, key = lambda x: x[0] + x[1] + x[2])
        minVector = bound_box[0]
        maxVector = bound_box[-1]

        parent = context.object.parent
        hide = parent.hide_get()
        parent.hide_set(False)
        parent.select_set(True)
        duplicate()
        move_to_collection(context, "Split Mesh Result")
        parent.hide_set(hide)

        context.object.parent.select_set(False)
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.separate(type="LOOSE")
        bpy.ops.object.mode_set(mode='OBJECT')
        sep_objs = context.selected_objects

        res_objs = []
        for sep_obj in sep_objs:
            bpy.ops.object.select_all(action='DESELECT')
            sep_obj.select_set(True)
            context.view_layer.objects.active = sep_obj
            duplicate()
            loose_obj = context.object
            bpy.ops.object.apply_all_modifiers()
            bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
            move_to_collection(context, "Split Mesh Loose")
            
            sep_obj.modifiers.new('split_mesh_modifier','DATA_TRANSFER')
            mod = sep_obj.modifiers['split_mesh_modifier']
            mod.use_loop_data = True
            mod.data_types_loops = {'CUSTOM_NORMAL'}
            mod.object = loose_obj
            
            bpy.ops.object.select_all(action='DESELECT')
            sep_obj.select_set(True)
            context.view_layer.objects.active = sep_obj
            
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            me = sep_obj.data
            bm = bmesh.from_edit_mesh(me)
            bm.faces.ensure_lookup_table()
            bm.faces[0].select_set(True)
            bpy.ops.mesh.select_linked(delimit={'SEAM'})
            face_sel = me.total_face_sel
            total_face = len(bm.faces)
            while face_sel < total_face:
                bpy.ops.mesh.separate(type="SELECTED")
                bm.faces.ensure_lookup_table()
                bm.faces[0].select_set(True)
                bpy.ops.mesh.select_linked(delimit={'SEAM'})
                face_sel = me.total_face_sel
                total_face = len(bm.faces)
            
            bmesh.update_edit_mesh(me)
            # bm.free()
            bpy.ops.object.mode_set(mode='OBJECT')
            res_objs.extend(context.selected_objects)

        bpy.data.collections['Split Mesh Loose'].hide_viewport = True
        
        rename(minVector, maxVector, res_objs)
        return {"FINISHED"}

class SplitRename(bpy.types.Operator):
    bl_idname = "splitmeshhelper.rename"
    bl_label = "Rename"
    bl_description = ""
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):

        return True

    def execute(self, context):
        sel_objs = context.selected_objects
        min_x = 0
        max_x = 0
        min_y = 0
        max_y = 0
        min_z = 0
        max_z = 0
        for sel_obj in sel_objs:
            bound_box = [sel_obj.matrix_world @ Vector(b) for b in sel_obj.bound_box]
            bound_box = sorted(bound_box, key = lambda x: x[0] + x[1] + x[2])
            min_x = min_x if min_x < bound_box[0][0] else bound_box[0][0]
            max_x = max_x if max_x > bound_box[1][0] else bound_box[1][0]
            min_y = min_y if min_y < bound_box[0][1] else bound_box[0][1]
            max_y = max_y if max_y > bound_box[1][1] else bound_box[1][1]
            min_z = min_z if min_z < bound_box[0][2] else bound_box[0][2]
            max_z = max_z if max_z > bound_box[1][2] else bound_box[1][2]
        minVector = Vector((min_x, min_y, min_z))
        maxVector = Vector((max_x, max_y, max_z))
        rename(minVector, maxVector, sel_objs)
        return {"FINISHED"}

class SplitMergeArmature(bpy.types.Operator):
    bl_idname = "splitmeshhelper.merge_armature"
    bl_label = "Merge Armature"
    bl_description = ""
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        
        return True

    def execute(self, context):
        active_arm = context.object
        sel_arms = [obj for obj in context.selected_objects if obj != active_arm]
        for sel_arm in sel_arms:
            for mesh in sel_arm.children:
                mod_list = [mod[1] for mod in mesh.modifiers.items() if mod[0] == "split_mesh_modifier"]
                if len(mod_list) == 0:
                    continue
                bpy.ops.object.select_all(action='DESELECT')
                mod = mod_list[0]
                loose_obj = mod.object
                mesh.modifiers.remove(mod)
                mesh.select_set(True)
                context.view_layer.objects.active = mesh
                bpy.ops.object.apply_all_modifiers()
                bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
                context.view_layer.objects.active = active_arm
                bpy.ops.object.parent_set(type='ARMATURE')
                mesh.modifiers.new('split_mesh_modifier','DATA_TRANSFER')
                mod = mesh.modifiers['split_mesh_modifier']
                mod.use_loop_data = True
                mod.data_types_loops = {'CUSTOM_NORMAL'}
                mod.object = loose_obj
            if len(sel_arm.children) == 0:
                bpy.data.objects.remove(sel_arm)
        return {"FINISHED"}

class PreviewPanel(bpy.types.Panel):
    bl_idname = "Preview_PT_Panel"
    bl_label = "Preview"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Split Mesh Helper"

    @classmethod
    def poll(self, context):
        if context.object and context.object.type == "MESH":
            return True
        return False

    def draw(self, context):
        pr = prefs()
        layout = self.layout
        row = layout.row()
        row.prop(pr, "expect_group")
        row = layout.row()
        row.prop(pr, "max_group")
        row = layout.row()
        row.operator("splitmeshhelper.preview", icon="EDITMODE_HLT")

class ConfirmPanel(bpy.types.Panel):
    bl_idname = "Confirm_PT_Panel"
    bl_label = "Confirm"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Split Mesh Helper"

    @classmethod
    def poll(self, context):
        if context.object and context.object.type == "MESH":
            return True
        return False

    def draw(self, context):
        pr = prefs()
        layout = self.layout
        row = layout.row()
        row.prop(pr, "order")
        row = layout.row()
        row.prop(pr, "reverse")
        row = layout.row()
        if pr.order == "0":
            row.label(text="Y Division")
        else:
            row.label(text="X Division")
        row = layout.row()
        row.prop(pr, "division1")
        row = layout.row()
        if pr.order == "2":
            row.label(text="Y Division")
        else:
            row.label(text="Z Division")
        row = layout.row()
        row.prop(pr, "division2")
        row = layout.row()
        row.label(text="Rename")
        """ name = context.object.name
        match_obj = re.match('LOD_1_Group_([0-9]*)_Sub_([0-9]*)__(.*)', name)
        if match_obj:
            pr.group_start = int(match_obj.group(1))
            pr.mat_index = int(match_obj.group(2))
            pr.mat_name = match_obj.group(3)
        else:
            pr.group_start = 1
            pr.mat_index = 0
            pr.mat_name = "none" """
        row = layout.row()
        row.prop(pr, "group_start")
        row = layout.row()
        row.prop(pr, "mat_index")
        row = layout.row()
        row.prop(pr, "mat_name")
        row = layout.row()
        layout.operator("splitmeshhelper.confirm", icon="MOD_CLOTH")

class ExtraPanel(bpy.types.Panel):
    bl_idname = "Extra_PT_Panel"
    bl_label = "Extra"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Split Mesh Helper"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(self, context):
        return True

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("splitmeshhelper.merge_armature", icon="OUTLINER_OB_ARMATURE")
        if not context.object:
            row.enabled = False
        if len(context.selected_objects) < 2:
            row.enabled = False
        sel_objs = [obj for obj in context.selected_objects if obj.type != "ARMATURE"]
        if len(sel_objs) > 0:
            row.enabled = False
        row = layout.row()
        row.operator("splitmeshhelper.rename", icon="SORTALPHA")
        if not context.object:
            row.enabled = False
        sel_objs = [obj for obj in context.selected_objects if obj.type != "MESH"]
        if len(sel_objs) > 0:
            row.enabled = False

classes = [
    SplitPreview,
    PreviewPanel,
    ToolPreferences,
    SplitConfirm,
    ConfirmPanel,
    ExtraPanel,
    SplitMergeArmature,
    SplitRename,
]

def register():
    for item in classes:
        bpy.utils.register_class(item)
    from .translation import translation_dict
    bpy.app.translations.register(bl_info['name'], translation_dict)

def unregister():
    bpy.app.translations.unregister(bl_info['name'])
    for item in classes:
        bpy.utils.unregister_class(item)

if __name__ == "__main__":
    register()