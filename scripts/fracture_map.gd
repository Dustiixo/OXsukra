class_name DeepbrewFractureMap
extends Control

signal cell_selected(gate: int, slot: int)

## X = ten parent gates / original timeline.
## Y = ten upward-indexed child-language addresses per parent.
## Every coloured cell is sourced from the verified COLOCRYPT Print.

var gates: Array = []
var active_gate := 0
var active_slot := 0
var inner_margin := Vector2(27, 16)


func _ready() -> void:
	custom_minimum_size = Vector2(440, 210)
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	mouse_filter = Control.MOUSE_FILTER_STOP


func set_data(gate_data: Array) -> void:
	gates = gate_data
	queue_redraw()


func set_active(gate: int, slot: int) -> void:
	active_gate = gate
	active_slot = slot
	queue_redraw()


func _cell_rect(gate: int, slot: int) -> Rect2:
	var width := maxf(20, (size.x - inner_margin.x * 2.0) / 10.0)
	var height := maxf(12, (size.y - inner_margin.y * 2.0) / 10.0)
	return Rect2(inner_margin.x + gate * width + 3, size.y - inner_margin.y - (slot + 1) * height + 2,
		width - 6, height - 4)


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color("0c1013"))
	if gates.size() != 10:
		return
	for gate in range(10):
		for slot in range(10):
			var splice = gates[gate]["splices"][slot]
			var rgb: Array = splice["display_rgb"]
			var col := Color(float(rgb[0])/255.0, float(rgb[1])/255.0, float(rgb[2])/255.0)
			var cell := _cell_rect(gate, slot)
			draw_rect(cell, col.darkened(0.38))
			var strength := minf(1.0, float(splice["mean_strength_pcm"]) / 12000.0)
			draw_rect(Rect2(cell.position, Vector2(cell.size.x * strength, 2)), col)
			if gate == active_gate and slot == active_slot:
				draw_rect(cell.grow(2), Color.WHITE, false, 2.0)
		var bottom := _cell_rect(gate, 0)
		var status := Color.html(str(gates[gate]["splices"][0]["status_colour"]))
		draw_line(Vector2(bottom.position.x, size.y - 8), Vector2(bottom.end.x, size.y - 8), status, 3)
	# A descending fault-line is a selection trace, not invented evidence.
	var focus := _cell_rect(active_gate, active_slot)
	var y := focus.get_center().y
	var left := Vector2(10, y)
	draw_line(focus.get_center(), left, Color("ed7bcb"), 1.3)
	draw_line(left, Vector2(10, size.y - 6), Color("a020f0"), 1.3)


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		for gate in range(10):
			for slot in range(10):
				if _cell_rect(gate, slot).grow(2).has_point(event.position):
					cell_selected.emit(gate, slot)
					accept_event()
					return
