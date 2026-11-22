extends Node2D
## UNDERBYTE foreground slice. Game owns all input; there are no OS hooks.
## Visuals and audio are original generated assets. The protagonist's mission remains unknown.

const SCREEN := Vector2(480.0, 270.0)
const GRAVITY := 710.0
const RUN_SPEED := 108.0
const JUMP_SPEED := 280.0
const MAX_FALL := 410.0
const GROUND_Y := 220.0
const PLAYER_HALF := 9.0
var save_path := "user://underbyte_save_v1.json"
var save_backup := "user://underbyte_save_v1.backup.json"
var save_temp := "user://underbyte_save_v1.pending.json"
const INVENTORY_CAP := 40

var world: Dictionary = {}
var recipes: Array = []
var words: Dictionary = {}
var atlas_player: Texture2D
var atlas_world: Texture2D
var logo: Texture2D
var music: AudioStreamPlayer

var player := Vector2(75.0, GROUND_Y)
var velocity := Vector2.ZERO
var grounded := true
var facing := 1
var animation_clock := 0.0
var camera_x := 0.0
var health := 5
var palette := 0
var player_name := "UNDERBYTE"
var mood := "curious"
var mood_timer := 0.0
var action_timer := 0.0
var jump_buffer := 0.0
var coyote := 0.0
var save_clock := 0.0
var play_seconds := 0.0
var status_message := ""
var status_seconds := 0.0
var ui_mode := ""
var selection := 0
var dialogue_line := 0
var intro_seen := false
var perspective_25d := false
var depth_lane := 0
var crystals := 0
var inv: Dictionary = {"shard": 0, "fiber": 0, "patch_kit": 0, "signal_key": 0, "lamp": 0, "device": 0}
var collected: Dictionary = {}
var depth_discoveries: Dictionary = {}
var device_cooldown := 0.0
var enemy_hp: Dictionary = {}
var enemy_position: Dictionary = {}
var enemy_direction: Dictionary = {}
var enemy_stagger: Dictionary = {}
var built_lamps: Array = []
var flags: Dictionary = {"talked": false, "relay": false, "device": false, "visited_gate": false, "completed": false}
var quests: Array = []
var checkpoint_x := 75.0
var hit_invulnerability := 0.0
var win_flash := 0.0
var held_pointer := false
var grab_pending := false
var grabbed := false
var grab_clock := 0.0
var grab_pointer := Vector2.ZERO
var last_grab_pointer := Vector2.ZERO
var throw_velocity := Vector2.ZERO
var rough_grabs := 0
var touch_controls: Dictionary = {} # Finger index -> button label
var touch_visible := false
var visual_warnings := 0
var music_enabled := true

func _notification(what: int) -> void:
	# Losing focus must always release a held character without sending OS input.
	if what == NOTIFICATION_WM_WINDOW_FOCUS_OUT:
		if grabbed: _release_grab()
		held_pointer = false
		grab_pending = false
		touch_controls.clear()

func _ready() -> void:
	if OS.get_cmdline_user_args().has("--isolated-test"):
		save_path = "user://underbyte_isolated_test.json"
		save_backup = "user://underbyte_isolated_test.backup.json"
		save_temp = "user://underbyte_isolated_test.pending.json"
	world = _read_dictionary("res://data/world.json")
	var recipe_data := _read_dictionary("res://data/recipes.json")
	recipes = recipe_data.get("recipes", [])
	words = _read_dictionary("res://data/dialogue.json")
	atlas_player = load("res://assets/player_atlas.png")
	atlas_world = load("res://assets/world_atlas.png")
	logo = load("res://assets/underbyte_logo.png")
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	for enemy in world.get("enemies", []):
		var eid := str(enemy.get("id", ""))
		enemy_hp[eid] = int(enemy.get("hp", 2))
		enemy_position[eid] = float(enemy.get("x", 0))
		enemy_direction[eid] = -1 if int(enemy.get("x", 0)) % 2 == 0 else 1
		enemy_stagger[eid] = 0.0
	music = AudioStreamPlayer.new()
	music.bus = "Master"
	music.volume_db = -23.0
	music.stream = load("res://assets/original_theme.wav")
	add_child(music)
	if music.stream is AudioStreamWAV:
		music.stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	music.play()
	load_game()
	if not intro_seen:
		_say("Move A/D, jump SPACE, interact E, mine/strike J. Your mission is still unknown.", 9.0)
	queue_redraw()

func _read_dictionary(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("Required content missing: " + path)
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if parsed is Dictionary:
		return parsed
	push_error("Content is not a dictionary: " + path)
	return {}

func _held(button: String) -> bool:
	if touch_controls.values().has(button):
		return true
	match button:
		"left": return Input.is_action_pressed("move_left")
		"right": return Input.is_action_pressed("move_right")
		"jump": return Input.is_action_pressed("jump")
		"up": return Input.is_action_pressed("move_up")
		"down": return Input.is_action_pressed("move_down")
	return false

func _input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		touch_visible = true
		if event.pressed:
			var label := _touch_hit(event.position)
			if label != "":
				touch_controls[event.index] = label
				if label in ["action", "strike", "inventory", "jump"]:
					_touch_action(label)
		else:
			touch_controls.erase(event.index)
		get_viewport().set_input_as_handled()
	if event is InputEventScreenDrag:
		touch_visible = true
		if touch_controls.has(event.index):
			var updated := _touch_hit(event.position)
			if updated in ["left", "right", "up", "down"]:
				touch_controls[event.index] = updated
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed and ui_mode == "":
			var game_cursor := get_global_mouse_position()
			if game_cursor.distance_to(_sprite_screen_center()) < 24.0:
				held_pointer = true
				grab_pending = true
				grab_clock = 0.0
				grab_pointer = game_cursor
				last_grab_pointer = game_cursor
		else:
			if held_pointer:
				_release_grab()
			held_pointer = false
			grab_pending = false
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_ESCAPE:
			if grabbed:
				_release_grab()
			elif ui_mode != "":
				ui_mode = ""
			else:
				ui_mode = "pause"
		elif ui_mode != "":
			_handle_menu_key(event)
		else:
			_handle_world_key(event)

func _handle_world_key(event: InputEventKey) -> void:
	match event.keycode:
		KEY_E, KEY_ENTER: _interact()
		KEY_J: _strike()
		KEY_C: _open_menu("craft")
		KEY_I: _open_menu("inventory")
		KEY_K: _open_menu("character")
		KEY_M: _open_menu("map")
		KEY_V:
			perspective_25d = not perspective_25d
			depth_lane = 0
			_say("Layered 2.5D perspective" if perspective_25d else "Side-on 2D perspective", 2.5)
		KEY_L: _place_lamp()
		KEY_U: _use_device()
		KEY_F5: save_game()
		KEY_R:
			player = Vector2(checkpoint_x, GROUND_Y)
			velocity = Vector2.ZERO
			_say("Returned to the last checkpoint.")
		KEY_F1: _open_menu("help")
		KEY_P: _open_menu("pause")
		KEY_N:
			music_enabled = not music_enabled
			music.stream_paused = not music_enabled

func _handle_menu_key(event: InputEventKey) -> void:
	if event.keycode in [KEY_DOWN, KEY_S, KEY_RIGHT, KEY_D]:
		selection += 1
	elif event.keycode in [KEY_UP, KEY_W, KEY_LEFT, KEY_A]:
		selection -= 1
	elif event.keycode in [KEY_ENTER, KEY_E, KEY_SPACE]:
		_menu_confirm()
	elif event.keycode in [KEY_I, KEY_K, KEY_C, KEY_M, KEY_P, KEY_BACKSPACE]:
		ui_mode = ""
	if ui_mode == "character": selection = posmod(selection, 4)
	if ui_mode == "craft": selection = posmod(selection, max(1, recipes.size()))

func _touch_action(button: String) -> void:
	if ui_mode != "":
		if button == "action": _menu_confirm()
		elif button == "inventory": ui_mode = ""
		return
	match button:
		"action": _interact()
		"strike": _strike()
		"inventory": _open_menu("inventory")
		"jump": jump_buffer = 0.17

func _touch_hit(p: Vector2) -> String:
	# Touch controls are part of the actual game (same input/actions as keyboard), not an emulator skin.
	# Logical viewport is 480x270. Godot remaps touch points to the viewport.
	if p.y < 170.0: return ""
	if p.x < 58.0: return "left"
	if p.x < 124.0: return "right"
	if p.x > 428.0: return "jump"
	if p.x > 370.0: return "strike"
	if p.x > 309.0: return "action"
	if p.x > 250.0: return "inventory"
	return ""

func _physics_process(delta: float) -> void:
	# Game simulation stops with focused menus, but continues during foreground play.
	if status_seconds > 0.0: status_seconds -= delta
	if mood_timer > 0.0: mood_timer -= delta
	if action_timer > 0.0: action_timer -= delta
	if device_cooldown > 0.0: device_cooldown -= delta
	if hit_invulnerability > 0.0: hit_invulnerability -= delta
	if win_flash > 0.0: win_flash -= delta
	animation_clock += delta
	if ui_mode != "":
		queue_redraw()
		return
	play_seconds += delta
	save_clock += delta
	if save_clock > 55.0:
		save_clock = 0.0
		save_game(false)
	if Input.is_action_just_pressed("jump"):
		jump_buffer = 0.14
	else:
		jump_buffer = maxf(0.0, jump_buffer - delta)
	if grounded: coyote = 0.12
	else: coyote = maxf(0.0, coyote - delta)
	if grab_pending and held_pointer:
		grab_clock += delta
		if grab_clock > 0.16:
			grabbed = true
			grab_pending = false
			mood = "surprised"
			mood_timer = 2.0
	if grabbed:
		_update_grab(delta)
	else:
		_update_player(delta)
	_update_enemies(delta)
	_check_enemy_collisions()
	_update_progress()
	camera_x = clampf(lerpf(camera_x, player.x - SCREEN.x * 0.4, minf(delta * 6.0, 1.0)), 0.0, maxf(0.0, float(world.get("width", 4800)) - SCREEN.x))
	queue_redraw()

func _update_player(delta: float) -> void:
	var direction := float(int(_held("right")) - int(_held("left")))
	if direction != 0.0: facing = 1 if direction > 0 else -1
	velocity.x = direction * RUN_SPEED
	if jump_buffer > 0.0 and coyote > 0.0:
		velocity.y = -JUMP_SPEED
		grounded = false
		jump_buffer = 0.0
		coyote = 0.0
		mood = "focused"
		mood_timer = 0.65
	velocity.y = minf(MAX_FALL, velocity.y + GRAVITY * delta)
	var old_y := player.y
	player.x = clampf(player.x + velocity.x * delta, 15.0, float(world.get("width", 4800)) - 18.0)
	player.y += velocity.y * delta
	grounded = false
	if velocity.y >= 0.0:
		var landed_y := GROUND_Y
		for platform in world.get("platforms", []):
			var px := float(platform.get("x", 0))
			var py := float(platform.get("y", 0))
			var pw := float(platform.get("w", 50))
			if player.x + 7 > px and player.x - 7 < px + pw and old_y <= py + 2 and player.y >= py:
				landed_y = minf(landed_y, py)
		if player.y >= landed_y:
			if velocity.y > 290.0 and old_y < landed_y - 15:
				mood = "surprised"
				mood_timer = 0.45
			player.y = landed_y
			velocity.y = 0.0
			grounded = true
	if perspective_25d:
		if Input.is_action_just_pressed("move_up"): depth_lane = maxi(-1, depth_lane - 1)
		if Input.is_action_just_pressed("move_down"): depth_lane = mini(1, depth_lane + 1)

func _update_grab(delta: float) -> void:
	last_grab_pointer = grab_pointer
	grab_pointer = get_global_mouse_position()
	var target := grab_pointer + Vector2(camera_x, 18)
	var change := target - player
	throw_velocity = change / maxf(delta, 0.001)
	player += change * minf(delta * 11.0, 0.88)
	player.x = clampf(player.x, 16.0, float(world.get("width", 4800)) - 17.0)
	player.y = clampf(player.y, 30.0, GROUND_Y - 5.0)
	velocity = Vector2.ZERO
	grounded = false

func _release_grab() -> void:
	if not grabbed: return
	grabbed = false
	grab_pending = false
	velocity.x = clampf(throw_velocity.x * 0.11, -160.0, 160.0)
	velocity.y = clampf(throw_velocity.y * 0.08, -140.0, 240.0)
	rough_grabs += 1 if throw_velocity.length() > 460.0 else 0
	mood = "annoyed" if rough_grabs >= 2 else "surprised"
	mood_timer = 1.8
	_say("OI! Mind the landing!" if rough_grabs >= 2 else "...well, that was unexpected.", 2.7)

func _sprite_screen_center() -> Vector2:
	return Vector2(player.x - camera_x, player.y - 15.0)

func _update_enemies(delta: float) -> void:
	for enemy in world.get("enemies", []):
		var id := str(enemy.get("id", ""))
		if int(enemy_hp.get(id, 0)) <= 0: continue
		var x := float(enemy_position.get(id, enemy.get("x", 0)))
		var origin := float(enemy.get("x", 0))
		var direction := int(enemy_direction.get(id, -1))
		if absf(player.x - x) < 96.0 and absf(player.y - GROUND_Y) < 80.0:
			direction = 1 if player.x > x else -1
		elif absf(x - origin) > 57.0:
			direction = -1 if x > origin else 1
		enemy_direction[id] = direction
		if float(enemy_stagger.get(id, 0.0)) > 0.0:
			enemy_stagger[id] = maxf(0.0, float(enemy_stagger[id]) - delta)
		else:
			enemy_position[id] = x + float(direction) * delta * (18.0 if str(enemy.get("kind")) == "wisp" else 26.0)

func _check_enemy_collisions() -> void:
	if hit_invulnerability > 0.0 or grabbed: return
	for enemy in world.get("enemies", []):
		var id := str(enemy.get("id", ""))
		if int(enemy_hp.get(id, 0)) <= 0: continue
		if absf(float(enemy_position.get(id, 0)) - player.x) < 15.0 and absf(GROUND_Y - player.y) < 28.0:
			health -= 1
			hit_invulnerability = 1.1
			velocity.y = -145.0
			mood = "hurt"
			mood_timer = 0.9
			_say("Ouch. That felt extremely unnecessary.", 2.1)
			if health <= 0: _respawn()
			break

func _respawn() -> void:
	health = 5
	player = Vector2(checkpoint_x, GROUND_Y)
	velocity = Vector2.ZERO
	_say("You're back. He seems annoyed that you noticed.", 4.0)
	save_game(false)

func _nearest_object(max_distance: float = 34.0) -> Dictionary:
	var selected: Dictionary = {}
	var best := max_distance
	for obj in world.get("objects", []):
		if obj.get("id") == "lost_device" and flags.get("device", false): continue
		var distance := absf(float(obj.get("x", 0)) - player.x)
		if distance < best:
			best = distance
			selected = obj
	return selected

func _nearest_resource(max_distance: float = 35.0) -> Dictionary:
	var best := max_distance
	var selected: Dictionary = {}
	for node in world.get("resources", []):
		if collected.has(str(node.get("id", ""))): continue
		var d := absf(float(node.get("x", 0.0)) - player.x)
		if d < best:
			best = d
			selected = node
	return selected

func _strike() -> void:
	if ui_mode != "" or grabbed: return
	action_timer = 0.23
	var enemy_found := false
	for enemy in world.get("enemies", []):
		var id := str(enemy.get("id", ""))
		if int(enemy_hp.get(id, 0)) <= 0: continue
		var distance := float(enemy_position.get(id, 0)) - player.x
		if absf(distance) <= 32.0 and (distance * facing >= -7.0):
			enemy_hp[id] = maxi(0, int(enemy_hp[id]) - 1)
			enemy_stagger[id] = 0.55
			if int(enemy_hp[id]) == 0:
				crystals += 1
				_say("Recovered a strange coin. The creature dissolves.")
			else:
				_say("Hit! Try another strike.", 1.1)
			enemy_found = true
			break
	if enemy_found: return
	var resource := _nearest_resource()
	if resource.size() > 0:
		var rid := str(resource.get("id", ""))
		var kind := str(resource.get("kind", "shard"))
		if _inventory_total() >= INVENTORY_CAP:
			_say("Pockets are full. Craft, use or place something first.")
			return
		collected[rid] = true
		inv[kind] = int(inv.get(kind, 0)) + 1
		mood = "happy"
		mood_timer = 0.7
		_say("Found " + kind + "! Press C for the workbench recipes.")
	else:
		_say("Nothing within tool range.", 1.0)

func _inventory_total() -> int:
	var total := 0
	for value in inv.values(): total += int(value)
	return total

func _interact() -> void:
	if ui_mode != "" or grabbed: return
	if perspective_25d and depth_lane != 0:
		for cache in world.get("depth_caches", []):
			var cache_id := str(cache.get("id", ""))
			if depth_discoveries.has(cache_id): continue
			if int(cache.get("lane", 0)) == depth_lane and absf(float(cache.get("x", 0)) - player.x) < 35.0:
				depth_discoveries[cache_id] = true
				inv["shard"] = int(inv.get("shard",0)) + 2
				_say("A seam between layers! Two shards. The perspective has consequences.",4.0)
				save_game(false)
				return
	var obj := _nearest_object()
	if obj.is_empty():
		_say("Nothing close enough to interact with.", 1.4)
		return
	match str(obj.get("kind", "")):
		"npc":
			flags["talked"] = true
			ui_mode = "dialogue"
			selection = 0
		"workbench": _open_menu("craft")
		"relay":
			if flags.get("relay", false):
				_say("Relay is already humming. Something farther east woke up.")
			elif int(inv.get("signal_key", 0)) >= 1:
				inv["signal_key"] = int(inv.get("signal_key", 0)) - 1
				flags["relay"] = true
				checkpoint_x = float(obj["x"])
				win_flash = 1.3
				_say("Relay online. Follow the vibration toward the EAST.", 5.0)
				save_game(false)
			else:
				_say("Sealed relay. Make a signal key: 3 shard + 1 fiber.", 4.0)
		"device":
			if flags.get("relay", false):
				flags["device"] = true
				inv["device"] = 1
				win_flash = 1.5
				_say("Recovered an unfamiliar device. His real purpose remains a secret.", 5.0)
				save_game(false)
			else:
				_say("The device isn't responding. The northern relay is silent.", 4.0)
		"portal":
			if str(obj.get("id")) == "gate_return":
				flags["visited_gate"] = true
				player.x = 35.0
				camera_x = 0.0
				_say("Tunnel loop completed. You return to the first region.")
			else:
				player.x = float(world.get("width", 4800)) - 45.0
				_say("A hidden passage folds the world around itself.")
			save_game(false)

func _open_menu(mode: String) -> void:
	ui_mode = mode
	selection = 0

func _menu_confirm() -> void:
	match ui_mode:
		"craft": _craft_recipe()
		"character":
			palette = posmod(selection, 4)
			_say("Character palette changed and saved.")
			save_game(false)
		"dialogue":
			dialogue_line += 1
			if dialogue_line >= words.get("intro", []).size():
				dialogue_line = 0
				ui_mode = ""
		"pause":
			save_game()
			ui_mode = ""
		"inventory", "map", "help", "end": ui_mode = ""

func _craft_recipe() -> void:
	if recipes.is_empty(): return
	var obj := _nearest_object(65.0)
	if obj.is_empty() or str(obj.get("kind", "")) != "workbench":
		_say("Craft at the workbench back near the start.", 2.7)
		return
	var recipe: Dictionary = recipes[clampi(selection, 0, recipes.size() - 1)]
	for id in recipe.get("requires", {}).keys():
		if int(inv.get(id, 0)) < int(recipe["requires"][id]):
			_say("Missing material: " + str(id) + ".", 1.5)
			return
	for id in recipe["requires"].keys():
		inv[id] = int(inv.get(id, 0)) - int(recipe["requires"][id])
	for id in recipe["grants"].keys():
		inv[id] = int(inv.get(id, 0)) + int(recipe["grants"][id])
	_say("Crafted " + str(recipe.get("label", "item")) + "!")
	save_game(false)

func _use_device() -> void:
	if not flags.get("device", false):
		_say("You haven't discovered the device yet.", 2.0)
		return
	if device_cooldown > 0.0:
		_say("Device needs to recharge.", 1.0)
		return
	device_cooldown = 8.0
	win_flash = 0.5
	var interrupted := 0
	for enemy in world.get("enemies",[]):
		var enemy_id := str(enemy.get("id", ""))
		if int(enemy_hp.get(enemy_id, 0)) > 0 and absf(float(enemy_position.get(enemy_id,0)) - player.x) < 96.0:
			enemy_stagger[enemy_id] = 3.2
			interrupted += 1
	_say("Pulse. " + str(interrupted) + " nearby creature(s) stunned.", 3.0)

func _place_lamp() -> void:
	if int(inv.get("lamp", 0)) > 0:
		inv["lamp"] = int(inv.get("lamp", 0)) - 1
		built_lamps.append(roundi(player.x))
		_say("Placed a lamp. It will still be here when you return.")
		save_game(false)
	else:
		_say("No lamp to place. Craft one at the workbench.")

func _update_progress() -> void:
	if flags.get("device", false) and flags.get("visited_gate", false) and not flags.get("completed", false):
		flags["completed"] = true
		win_flash = 2.8
		ui_mode = "end"
		save_game(false)

func _say(message: String, duration: float = 3.4) -> void:
	status_message = message
	status_seconds = duration

func _to_save() -> Dictionary:
	return {
		"schema": 1, "world_seed": world.get("seed", 73103),
		"player": {"x": player.x, "y": player.y, "palette": palette, "name": player_name, "health": health, "mood": mood},
		"collected": collected, "depth_discoveries": depth_discoveries, "inventory": inv, "enemy_hp": enemy_hp, "enemy_position": enemy_position,
		"flags": flags, "lamps": built_lamps, "checkpoint_x": checkpoint_x,
		"perspective_25d": perspective_25d, "depth_lane": depth_lane,
		"crystals": crystals, "rough_grabs": rough_grabs, "play_seconds": play_seconds, "intro_seen": true
	}

func save_game(notify: bool = true) -> void:
	var target := ProjectSettings.globalize_path(save_path)
	var tmp := ProjectSettings.globalize_path(save_temp)
	var backup := ProjectSettings.globalize_path(save_backup)
	var new_data := JSON.stringify(_to_save(), "  ")
	var file := FileAccess.open(save_temp, FileAccess.WRITE)
	if file == null:
		_say("Couldn't write save. Progress remains in this session.", 4.0)
		return
	file.store_string(new_data)
	file.flush()
	file.close()
	# Verify temporary content before touching the last good save.
	var verified: Variant = JSON.parse_string(FileAccess.get_file_as_string(save_temp))
	if not (verified is Dictionary) or int(verified.get("schema", -1)) != 1:
		_say("Save validation failed. Old save preserved.", 4.0)
		return
	if FileAccess.file_exists(save_path):
		var backup_result := DirAccess.copy_absolute(target, backup)
		if backup_result != OK:
			_say("Backup failed. Old save preserved.", 4.0)
			return
		var remove_result := DirAccess.remove_absolute(target)
		if remove_result != OK:
			_say("Could not replace save. Old save preserved.", 4.0)
			return
	var code := DirAccess.rename_absolute(tmp, target)
	if code != OK:
		if FileAccess.file_exists(save_backup):
			DirAccess.copy_absolute(backup, target)
		_say("Couldn't finalize save; recovered backup (code " + str(code) + ").", 4.0)
		return
	if notify: _say("World and character saved.", 2.0)

func load_game() -> void:
	var data: Variant = null
	for path in [save_path, save_backup]:
		if not FileAccess.file_exists(path): continue
		data = JSON.parse_string(FileAccess.get_file_as_string(path))
		if data is Dictionary and int(data.get("schema", -1)) == 1 and int(data.get("world_seed", -1)) == int(world.get("seed", 0)):
			break
		data = null
	if not (data is Dictionary): return
	var ch: Dictionary = data.get("player", {})
	player = Vector2(clampf(float(ch.get("x", 75)), 15, float(world.get("width", 4800)) - 18), clampf(float(ch.get("y", GROUND_Y)), 30, GROUND_Y))
	palette = clampi(int(ch.get("palette", 0)), 0, 3)
	player_name = str(ch.get("name", "UNDERBYTE")).substr(0, 18)
	health = clampi(int(ch.get("health", 5)), 1, 5)
	mood = str(ch.get("mood", "curious"))
	collected = data.get("collected", {})
	depth_discoveries = data.get("depth_discoveries", {})
	for id in inv.keys(): inv[id] = maxi(0, int(data.get("inventory", {}).get(id, 0)))
	for id in enemy_hp.keys(): enemy_hp[id] = maxi(0, int(data.get("enemy_hp", {}).get(id, enemy_hp[id])))
	for id in enemy_position.keys(): enemy_position[id] = float(data.get("enemy_position", {}).get(id, enemy_position[id]))
	for id in flags.keys(): flags[id] = bool(data.get("flags", {}).get(id, false))
	built_lamps = data.get("lamps", [])
	checkpoint_x = clampf(float(data.get("checkpoint_x", 75)), 15, float(world.get("width", 4800)) - 18)
	perspective_25d = bool(data.get("perspective_25d", false))
	depth_lane = clampi(int(data.get("depth_lane", 0)), -1, 1)
	crystals = maxi(0, int(data.get("crystals", 0)))
	rough_grabs = maxi(0, int(data.get("rough_grabs", 0)))
	play_seconds = maxf(0.0, float(data.get("play_seconds", 0)))
	intro_seen = bool(data.get("intro_seen", true))
	_say("Continuity restored. The little guy remembers.", 3.5)

func _region_for_world_x(world_x: float) -> Dictionary:
	var index := clampi(int(floor(world_x / 300.0)), 0, world.get("regions", []).size() - 1)
	return world.get("regions", [])[index]

func _draw() -> void:
	_draw_sky()
	_draw_terrain()
	_draw_world_actors()
	_draw_player()
	_draw_hud()
	if touch_visible: _draw_touch()
	if ui_mode != "": _draw_panel()
	if win_flash > 0.0:
		draw_rect(Rect2(0,0,480,270), Color(0.83,0.92,1.0, minf(0.28, win_flash*0.14)))

func _draw_sky() -> void:
	var center_region := _region_for_world_x(player.x)
	var top := Color("#10182b")
	var bottom := Color(str(center_region.get("tone", "#394a5e")))
	for i in range(14):
		var factor := float(i) / 13.0
		draw_rect(Rect2(0,i*18,480,19), top.lerp(bottom,factor), true)
	for i in range(45):
		var sx := fposmod(float(i*79+13) - camera_x*0.11, 510.0) - 14.0
		var sy := 8.0 + float((i*43+17)%105)
		draw_rect(Rect2(sx,sy, 1 if i%4 else 2, 1),Color(0.8,0.9,0.93, 0.55 if i%3 else 0.88))
	# Far skyline — multiple parallax planes.
	for layer in range(3):
		var speed: float = [0.12,0.23,0.39][layer]
		var color: Color = [Color("#22314b"),Color("#273951"),Color("#2d4056")][layer]
		for i in range(24):
			var x := fposmod(float(i*57+layer*30)-camera_x*speed, 580.0)-70
			var h := float((i*29+layer*13)%49)+20.0
			draw_rect(Rect2(x, 185-h+layer*17, 26+(i%3)*15,h+40),color)
			if layer==2 and i%4==0:
				draw_rect(Rect2(x+5,183-h+layer*17+12,3,4),Color("#8fc2c7"))
	# distant fixed moon
	draw_circle(Vector2(370-camera_x*0.02,45),18,Color("#94a8b3"))
	draw_circle(Vector2(375-camera_x*0.02,40),16,Color("#a5b7be"))
	for i in range(8):
		var x := fposmod(float(i*155+40)-camera_x*0.55,560.0)-40
		draw_rect(Rect2(x,183,5,37),Color("#1b3240"))
		draw_rect(Rect2(x-9,182,24,3),Color("#1b3240"))

func _draw_terrain() -> void:
	# Single game-state topology; perspective mode draws a skewed extra depth plane.
	if perspective_25d:
		var skew_points := PackedVector2Array([Vector2(-30,218),Vector2(505,218),Vector2(467,265),Vector2(-55,265)])
		draw_colored_polygon(skew_points, Color("#345362"))
		for i in range(-1,12):
			var px := float(i*57)-fposmod(camera_x,57.0)
			draw_line(Vector2(px,218),Vector2(px-28,270), Color("#527683"),1)
		for j in range(6):
			draw_line(Vector2(0,218+j*9),Vector2(480,218+j*9),Color("#476877"),1)
	else:
		draw_rect(Rect2(0, GROUND_Y-1, SCREEN.x,SCREEN.y-GROUND_Y+1),Color("#263b47"))
		draw_rect(Rect2(0,GROUND_Y-2,SCREEN.x,4), Color("#77917c"))
		for i in range(32):
			var x := fposmod(float(i*31)-camera_x,520.0)-20
			var y := 229.0+float((i*47)%36)
			draw_rect(Rect2(x,y,9,2), Color("#435c63"))
		for i in range(31):
			var x := fposmod(float(i*41+15)-camera_x,530.0)-25
			draw_rect(Rect2(x,GROUND_Y-5,2,4),Color("#698f79"))
	for platform in world.get("platforms", []):
		var x := float(platform.get("x", 0))-camera_x
		if x > 530 or x < -120: continue
		var y := float(platform.get("y", 0))
		var width := float(platform.get("w", 60))
		draw_rect(Rect2(x,y,width,6),Color("#688c85"))
		draw_rect(Rect2(x,y+5,width,8),Color("#354e60"))
		for i in range(int(width / 15)):
			draw_rect(Rect2(x+float(i*15),y+5,1,7),Color("#253e4d"))
	# Regional light columns, landmarks, and entry signage.
	for region in world.get("regions", []):
		var x := float(region.get("x_start", 0))-camera_x
		if x > 510 or x < -100: continue
		draw_rect(Rect2(x,154,2,66),Color("#3b5767"))
		draw_rect(Rect2(x-3,151,8,8),Color("#b5d5b3") if bool(region.get("is_cardinal",false)) else Color("#537c8b"))
		if bool(region.get("is_cardinal",false)):
			_text(str(region.get("title", "")),Vector2(x+12,162),Color("#a7d6d4"),9)
	for x_world in built_lamps:
		var x := float(x_world)-camera_x
		if x < -10 or x > 490: continue
		draw_circle(Vector2(x,197),22,Color(1.0,0.76,0.35,0.09))
		draw_rect(Rect2(x-2,199,4,20),Color("#d0b77d"))
		draw_rect(Rect2(x-4,195,8,7),Color("#ffe2a4"))

func _atlas_draw(index: int, x: float, y: float, opacity: float=1.0, size:float=32.0) -> void:
	if atlas_world == null: return
	draw_texture_rect_region(atlas_world, Rect2(x-size*0.5,y-size*0.5,size,size),Rect2(index*32,0,32,32),Color(1,1,1,opacity))

func _draw_world_actors() -> void:
	for node in world.get("resources", []):
		if collected.has(str(node.get("id", ""))): continue
		var x := float(node.get("x", 0))-camera_x
		if x < -24 or x > 504: continue
		var y := float(node.get("y", GROUND_Y))-12.0
		var idx := 2 if str(node.get("kind")) == "shard" else 3
		_atlas_draw(idx, x, y, 1.0, 24)
	for obj in world.get("objects", []):
		if str(obj.get("id")) == "lost_device" and flags.get("device", false):continue
		var x := float(obj.get("x", 0))-camera_x
		if x < -32 or x > 512: continue
		var idx: int = int({"relay":4,"workbench":5,"device":6,"npc":7,"portal":8}.get(str(obj.get("kind")),9))
		var y := float(obj.get("y",220))-16.0
		_atlas_draw(int(idx), x, y, 1.0, 32)
		if str(obj.get("kind")) == "relay" and flags.get("relay",false):
			draw_circle(Vector2(x,y),17,Color(0.62,0.95,0.9,0.21))
	if perspective_25d:
		for cache in world.get("depth_caches", []):
			var id := str(cache.get("id", ""))
			if depth_discoveries.has(id): continue
			var cache_x := float(cache.get("x", 0))-camera_x
			if cache_x < -30 or cache_x > 510: continue
			var cache_y := 194.0 + float(cache.get("lane",0))*12.0
			_atlas_draw(9, cache_x, cache_y, 0.85, 24)
		for cache in world.get("depth_caches", []):
			var cache_id := str(cache.get("id", ""))
			if depth_discoveries.has(cache_id): continue
			if int(cache.get("lane",0)) == depth_lane and absf(float(cache.get("x",0))-player.x)<35:
				_text("[E] LAYER SECRET", Vector2(330,185), Color("#d8c7f5"),9)
	for enemy in world.get("enemies", []):
		var id := str(enemy.get("id", ""))
		if int(enemy_hp.get(id,0)) <= 0: continue
		var x := float(enemy_position.get(id,0))-camera_x
		if x < -30 or x > 510: continue
		var sway := sin(animation_clock*3.0 + float(enemy.get("x",0))*0.02)*3.0
		_atlas_draw(1 if str(enemy.get("kind"))=="wisp" else 0,x,204+sway,1.0,32)

func _draw_player() -> void:
	if atlas_player == null: return
	var frame := 0
	if grabbed: frame = 7
	elif mood == "hurt" and mood_timer > 0.0: frame = 10
	elif mood == "annoyed" and mood_timer > 0.0: frame = 7
	elif action_timer > 0.0: frame = 5
	elif not grounded and velocity.y < 0.0: frame = 3
	elif not grounded and velocity.y >= 0.0: frame = 4
	elif absf(velocity.x) > 1.0: frame = 1 + int(floor(animation_clock*9.0)) % 2
	elif mood == "happy" and mood_timer > 0.0: frame = 8
	elif fposmod(animation_clock,11.0) > 9.0: frame = 11
	var px := player.x-camera_x
	var py := player.y-32.0
	if perspective_25d:
		py += float(depth_lane)*7.0
		px += float(depth_lane)*5.0
	draw_ellipse_shadow(Vector2(px,GROUND_Y),9.0)
	if hit_invulnerability > 0 and int(animation_clock*14)%2 == 0:
		return
	draw_texture_rect_region(atlas_player,Rect2(roundf(px)-16.0,roundf(py),32,32),Rect2(frame*32,palette*32,32,32))
	if facing < 0:
		draw_rect(Rect2(px+9,py+14,5,2),Color("#a94d65"))
	else:
		draw_rect(Rect2(px-14,py+14,5,2),Color("#a94d65"))
	if grabbed:
		draw_line(Vector2(px,py+5),grab_pointer,Color("#d6eab3"),1.0)

func draw_ellipse_shadow(center: Vector2, radius:float) -> void:
	draw_rect(Rect2(center.x-radius,center.y+2.0,radius*2,2.0),Color(0.05,0.12,0.18,0.45))

func _font() -> Font:
	return ThemeDB.fallback_font

func _text(s: String, p: Vector2, color: Color=Color("#f2f2e3"), size:int=10) -> void:
	draw_string(_font(),p,s,HORIZONTAL_ALIGNMENT_LEFT,-1,size,color)

func _draw_hud() -> void:
	var region := _region_for_world_x(player.x)
	draw_rect(Rect2(4,4,190,30),Color(0.07,0.10,0.17,0.83))
	for i in range(5):
		_text("♥" if i < health else "·",Vector2(11+i*15,18),Color("#ea7889") if i<health else Color("#495268"),14)
	_text(str(region.get("title","?")),Vector2(91,17),Color("#d0e5d8"),9)
	_text("2.5D" if perspective_25d else "2D",Vector2(164,29),Color("#70cdd8"),9)
	if crystals>0:
		_text("✦"+str(crystals),Vector2(12,29),Color("#f5cd8b"),10)
	var task := "MEET THE WANDERER" if not flags.get("talked",false) else ("CRAFT A SIGNAL KEY" if not flags.get("relay",false) else ("RECOVER THE DEVICE" if not flags.get("device",false) else ("REACH THE OUTER TUNNEL" if not flags.get("visited_gate",false) else "THE WORLD REMAINS OPEN")))
	draw_rect(Rect2(229,5,247,29),Color(0.07,0.10,0.17,0.77))
	_text("NEXT: "+task,Vector2(235,18),Color("#d9e7d6"),9)
	_text("J  strike/mine   E  use   I  pack   F1  help",Vector2(235,29),Color("#8eacbd"),8)
	var close := _nearest_object()
	if close.size()>0 and ui_mode=="":
		var label := str(close.get("kind", "object")).to_upper()
		var px := clampf(float(close.get("x",0))-camera_x-20,25,405)
		_text("[E] "+label,Vector2(px,174),Color("#f1d297"),9)
	if status_seconds>0.0 and ui_mode=="":
		draw_rect(Rect2(10,235,460,24),Color(0.06,0.09,0.17,0.91))
		_text(status_message.substr(0,75),Vector2(17,251),Color("#e6dfc4"),10)
	# Small HUD, never covers the center of play.
	if not touch_visible:
		_text("A/D MOVE  SPACE JUMP  V VIEW  C CRAFT  K LOOK  F5 SAVE",Vector2(65,267),Color("#718c9a"),8)

func _draw_touch() -> void:
	# Functional touchscreen zones, visually subdued, only drawn on touch devices.
	var hints := [
		[Rect2(7,211,48,48),"◀"], [Rect2(66,211,48,48),"▶"],
		[Rect2(260,214,49,45),"I"], [Rect2(319,214,49,45),"E"],
		[Rect2(378,214,45,45),"B"], [Rect2(434,209,43,50),"A"]]
	for hint in hints:
		draw_rect(hint[0],Color(0.04,0.09,0.14,0.55),true)
		draw_rect(hint[0],Color(0.54,0.75,0.78,0.4),false,1)
		_text(str(hint[1]),hint[0].position+Vector2(17,30),Color("#d5e6e5"),13)

func _draw_panel() -> void:
	draw_rect(Rect2(46,34,388,194),Color(0.06,0.09,0.16,0.95))
	draw_rect(Rect2(46,34,388,194),Color("#6d91a0"),false,2)
	var heading: String = str({"dialogue":"TALK", "inventory":"SATCHEL", "craft":"WORKBENCH", "character":"YOUR LITTLE GUY", "map":"THE CONNECTED WORLD", "pause":"PAUSED", "help":"CONTROLS", "end":"A SMALL COMPLETION"}.get(ui_mode,"UNDERBYTE"))
	_text(str(heading),Vector2(64,55),Color("#b2e8da"),16)
	_text("ESC CLOSE  ·  ENTER SELECT",Vector2(290,53),Color("#8ea8ad"),9)
	match ui_mode:
		"dialogue":
			var sentences: Array = words.get("intro",[])
			if not sentences.is_empty():
				var line := str(sentences[clampi(dialogue_line,0,sentences.size()-1)])
				_draw_wrapped(line, 68,83,330,15,Color("#eee3c2"))
			_text("The wanderer watches him. Nobody knows his plan.",Vector2(69,180),Color("#82a9b4"),10)
		"inventory":
			var row := 0
			for id in inv.keys():
				_text(str(id).capitalize().rpad(16," ")+"×"+str(inv[id]),Vector2(69,83+row*19),Color("#e0e5d8"),12)
				row += 1
			_text("L place lamp · C opens crafting · 40-slot carry cap",Vector2(68,214),Color("#9eb9bd"),10)
		"craft":
			for i in range(recipes.size()):
				var recipe:Dictionary = recipes[i]
				var description := str(recipe.get("label", ""))
				var needs:Dictionary = recipe.get("requires",{})
				for id in needs.keys(): description += "  "+str(id)+":"+str(needs[id])
				_text(("> " if selection == i else "  ")+description,Vector2(69,85+i*37),Color("#f4d894") if selection==i else Color("#cad9d8"),11)
			_text("Must stand beside a workbench to craft.",Vector2(69,207),Color("#8ea9b8"),10)
		"character":
			for i in range(4):
				var palettes := ["AMBER","CYAN","VIOLET","FOREST"]
				_text(("> " if selection==i else "  ")+palettes[i],Vector2(70,82+i*29),Color("#f4db9b") if selection==i else Color("#c2d2d7"),12)
				if atlas_player: draw_texture_rect_region(atlas_player,Rect2(285,73+i*29,24,24),Rect2(0,i*32,32,32))
			_text("Changing palette changes the actual player sprite.",Vector2(70,208),Color("#90acb9"),10)
		"map":
			for region in world.get("regions",[]):
				var index := int(region.get("index",0))
				var x := 67+int(index%8)*44
				var y := 91+int(index/8)*50
				draw_rect(Rect2(x,y,39,32),Color("#507a85") if index==int(player.x/300) else Color("#273d4e"))
				_text(str(region.get("id","")),Vector2(x+4,y+18),Color("#e5e0cf"),8)
			_text("4 cardinal regions · 12 connector regions · outer tunnel",Vector2(70,210),Color("#a4bbba"),10)
		"pause":
			_text("The world is paused. No desktop programs are controlled.",Vector2(68,92),Color("#e3e5d9"),11)
			_text("ENTER save and resume  /  ESC resume",Vector2(68,135),Color("#d7d6b1"),12)
		"help":
			var tips := ["A/D or arrows: move   Space: jump", "J: strike or mine nearby material   E: interact", "C: craft   I: inventory   K: customize", "V: 2D ↔ layered 2.5D   M: map", "F5: save   L: lamp   U: device pulse   N: music", "Mouse: click-hold character to levitate and release", "ESC: pause / close menu   R: return to checkpoint"]
			for i in range(tips.size()): _text(tips[i],Vector2(69,79+i*20),Color("#dce8db"),10)
		"end":
			_text("A relay repaired. A device recovered. A long route explored.",Vector2(67,92),Color("#f1dfa8"),11)
			_text("His private mission remains a mystery.",Vector2(67,118),Color("#e4d6c5"),13)
			_text("The world stays open for exploration, crafting and secrets.",Vector2(67,151),Color("#96bac1"),11)
			_text("ENTER to return to the living world",Vector2(67,207),Color("#c8e4d2"),11)

func _draw_wrapped(content: String, x: int, start_y: int, max_width: int, line_height: int, color: Color) -> void:
	var row := ""
	var y := start_y
	for word in content.split(" "):
		var trial := row + (" " if row != "" else "") + word
		if trial.length()*6 > max_width and row != "":
			_text(row,Vector2(x,y),color,12)
			y += line_height
			row = word
		else: row = trial
	if row != "": _text(row,Vector2(x,y),color,12)
