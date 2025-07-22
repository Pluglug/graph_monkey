# import bpy, weakref

# _popup_ref = None
# def set_popup(p): global _popup_ref; _popup_ref = weakref.ref(p)
# def get_popup():   return _popup_ref() if _popup_ref else None
# def clear_popup(): set_popup(None)


# class WM_OT_popup_calc(bpy.types.Operator):
#     bl_idname = "wm.popup_calc"
#     bl_label  = "Calculator"

#     expr: bpy.props.StringProperty(default="")

#     _ptr        = None        # PointerRNA to container (ID か PropertyGroup)
#     _prop       = None        # Property definition
#     _prop_index = -1          # Vector要素番号
#     _sub_path   = ""          # ID からの相対パス（.eevee など）
#     _id_owner   = None        # 最終的に書き込む ID オブジェクト

#     # ───────── poll
#     @classmethod
#     def poll(cls, ctx):
#         if cls._ptr:  # パネルダイアログでOKを押した場合  # FIXME: メニュー実行時に前回の_ptrが残っている。
#             print("poll: already open", cls._ptr)
#             return True
#         pptr  = getattr(ctx, "button_pointer", None)
#         pprop = getattr(ctx, "button_prop",    None)
#         return pptr and pprop and pprop.type in {'INT', 'FLOAT'}

#     # ───────── invoke
#     def invoke(self, ctx, _evt):
#         # FIXME: 前回入力した数値が残っている
#         cls = self.__class__
#         cls._ptr        = getattr(ctx, "button_pointer", None)
#         cls._prop       = getattr(ctx, "button_prop",    None)
#         cls._prop_index = getattr(ctx, "button_prop_index", -1)

#         # 相対パスは try/except で安全に
#         try:
#             cls._sub_path = cls._ptr.path_from_id() or ""
#         except Exception:      # SunLight などで失敗
#             cls._sub_path = ""

#         # 書き込み先 ID
#         cls._id_owner = cls._ptr.id_data or cls._ptr   # ラッパなら id_data、本体なら自分

#         # UI 表示用（失敗時は簡易的に repr）
#         id_path = f'bpy.data.{cls._id_owner.__class__.__name__.lower()}s["{cls._id_owner.name}"]'
#         self.path_display = f"{id_path}{cls._sub_path}.{cls._prop.identifier}"
#         if cls._prop_index != -1:
#             self.path_display += f"[{cls._prop_index}]"

#         set_popup(self)
#         return ctx.window_manager.invoke_props_dialog(self, width=240)

#     # ───────── draw
#     def draw(self, _ctx):
#         col = self.layout.column()
#         col.label(text=self.path_display, icon='RNA')
#         col.prop(self, "expr", text="")
#         grid = col.grid_flow(columns=3, align=True)
#         for ch in "7894561230.+-*/":
#             grid.operator("wm.calc_key", text=ch).char = ch
#         grid.operator("wm.calc_key", text="←").char = "BACK"

#     # ───────── execute
#     def execute(self, _ctx):
#         # ① 数式→数値
#         try:
#             val = eval(self.expr, {}, {})
#         except Exception:
#             self.report({'ERROR'}, "Invalid expression")
#             return {'CANCELLED'}
#         if self._prop.type == 'INT':
#             val = int(round(val))

#         # ② パス解決：ID → sub_path (=PropertyGroup) → prop
#         try:
#             container = (self._id_owner.path_resolve(self._sub_path, False)
#                          if self._sub_path else self._id_owner)
#         except Exception:
#             container = self._ptr               # 最終手段

#         # ③ 書き戻し
#         try:
#             if self._prop_index != -1:
#                 vec = list(getattr(container, self._prop.identifier))
#                 vec[self._prop_index] = val
#                 setattr(container, self._prop.identifier, vec)
#             else:
#                 setattr(container, self._prop.identifier, val)
#         except Exception as exc:
#             self.report({'ERROR'}, f"Write-back failed: {exc}")
#             return {'CANCELLED'}

#         # ④ デプスグラフ更新で UI 反映
#         bpy.context.evaluated_depsgraph_get().update()
#         clear_popup()
#         return {'FINISHED'}


# class WM_OT_calc_key(bpy.types.Operator):
#     bl_idname = "wm.calc_key"
#     bl_label  = "Calc Key"
#     char: bpy.props.StringProperty()

#     def execute(self, _ctx):
#         popup = get_popup()
#         if not popup:
#             self.report({'ERROR'}, "Calculator not running")
#             return {'CANCELLED'}
#         popup.expr = popup.expr[:-1] if self.char == "BACK" else popup.expr + self.char
#         return {'FINISHED'}


# def _draw_calc_entry(self, _ctx):
#     self.layout.separator()
#     self.layout.operator("wm.popup_calc", icon='TOPBAR')


# # ---------------- register helpers
# _classes = (WM_OT_popup_calc, WM_OT_calc_key)
# def register():
#     for c in _classes: bpy.utils.register_class(c)
#     bpy.types.UI_MT_button_context_menu.append(_draw_calc_entry)

# def unregister():
#     bpy.types.UI_MT_button_context_menu.remove(_draw_calc_entry)
#     for c in _classes[::-1]: bpy.utils.unregister_class(c)

# if __name__ == "__main__":
#     register()

# # FIXME:
# # Python: Traceback (most recent call last):
# #   File "\Text", line 98, in execute
# #   File "\Text", line 6, in clear_popup
# #   File "\Text", line 4, in set_popup
# # TypeError: cannot create weak reference to 'NoneType' object
