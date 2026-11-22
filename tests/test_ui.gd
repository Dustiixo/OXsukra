extends SceneTree

var passed := 0
var failed := 0


func _initialize() -> void:
	call_deferred("run_flow")


func run_flow() -> void:
	var scene: Control = load("res://scenes/main.tscn").instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	await process_frame
	var editor: CodeEdit = scene.get("source_editor")
	var options: OptionButton = scene.get("effect_select")
	var duration: SpinBox = scene.get("duration_spin")
	var tabs: TabContainer = scene.get("view_stack")
	var engine = scene.get("engine")
	var graph: GraphEdit = scene.get("graph")
	print("VISUAL METRICS root=", scene.size, " graph=", graph.size, " scroll=", graph.scroll_offset)
	for id in ["trigger", "effect", "evidence"]:
		var node: GraphNode = graph.get_node(id)
		print("VISUAL NODE ", id, " offset=", node.position_offset, " size=", node.size, " position=", node.position)
	check(editor != null and editor.text.contains("deepbrew.behavior.v1"), "UI loads real sample source")
	check(options != null and options.item_count == 3, "UI exposes typed effects")
	options.select(1) # open
	duration.value = 1500
	scene.call("_preview")
	check(engine.last_preview.get("is_change", false), "UI stages actual patch")
	check(tabs.current_tab == 1, "UI reveals exact source preview")
	scene.call("_apply")
	check(engine.applied, "UI applies to private working revision")
	check(editor.text.contains('"effect": "open"'), "UI reflects actual applied source")
	scene.call("_test")
	check(tabs.current_tab == 2, "UI opens visual sandbox")
	var after: Label = scene.get("after_state")
	check(after.text == "STATE: OPEN", "sandbox visual shows observed open state")
	scene.call("_rollback")
	check(not engine.applied and editor.text.contains('"effect": "closed"'), "UI restores exact original state")
	check(scene.get("status_label").text.contains("ROLLBACK VERIFIED"), "UI reports verification")
	print("DEEPBREW UI RESULT: %d passed, %d failed" % [passed, failed])
	scene.queue_free()
	quit(1 if failed else 0)


func check(condition: bool, description: String) -> void:
	if condition:
		passed += 1
		print("PASS  ", description)
	else:
		failed += 1
		push_error("FAIL  " + description)
