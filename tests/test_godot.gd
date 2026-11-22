extends SceneTree
## Engine integration smoke: run with --headless --path PROJECT --script res://tests/test_godot.gd -- --isolated-test
## Uses isolated save names so the player's real save is untouched.
var fails: int = 0

func _initialize() -> void:
	call_deferred("_verify")

func _check(condition: bool, context: String) -> void:
	if condition:
		print("PASS: ", context)
	else:
		fails += 1
		push_error("FAIL: " + context)

func _verify() -> void:
	var template: PackedScene = load("res://scenes/game.tscn")
	_check(template != null, "game scene loads")
	if template == null:
		quit(1)
		return
	var game = template.instantiate()
	root.add_child(game)
	await process_frame
	_check(game.atlas_player != null, "actual pixel sprite texture loaded")
	_check(game.world.get("regions",[]).size() == 16, "all 16 regions imported")
	_check(game.player.x > 0 and game.player.y > 0, "starting character position is visible")
	game.player = Vector2(118, 220)
	game.inv["shard"] = 3
	game.inv["fiber"] = 1
	game.ui_mode = "craft"
	game.selection = 1
	game._craft_recipe()
	_check(game.inv["signal_key"] == 1 and game.inv["shard"] == 0, "actual crafting consumes material and creates signal key")
	game.ui_mode = ""
	game.player.x = 1317
	game._interact()
	_check(game.flags["relay"] == true and game.inv["signal_key"] == 0, "relay activation consumes key")
	game.player.x = 2602
	game._interact()
	_check(game.flags["device"] == true and game.inv["device"] == 1, "device is recovered")
	game.collected["test_resource"] = true
	game.palette = 2
	game.player.x = 1980
	game.save_game(false)
	game.player.x = 90
	game.palette = 0
	game.collected.clear()
	game.load_game()
	_check(game.palette == 2 and absf(game.player.x - 1980) < 0.01, "save and load restore position and palette")
	_check(game.collected.has("test_resource") and game.flags["device"], "save and load restore collection and quest flags")
	for path in [game.save_path, game.save_backup, game.save_temp]:
		if FileAccess.file_exists(path): DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	game.queue_free()
	print("GODOT INTEGRATION SMOKE FAILURES: ", fails)
	quit(0 if fails == 0 else 1)
