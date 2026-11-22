extends SceneTree

## Independent engine process. Args: -- <absolute mod file> <expected SHA256>
## Does NOT import DeepBrew scripts or call its internal simulation.

func _initialize() -> void:
	call_deferred("run_world")


func run_world() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2:
		_fail("expected a mod path and its approved SHA-256")
		return
	var path: String = args[0]
	var expected_sha: String = args[1]
	if not expected_sha.is_valid_hex_number(false) or expected_sha.length() != 64:
		_fail("malformed expected digest")
		return
	if not FileAccess.file_exists(path):
		_fail("mod file missing")
		return
	var bytes := FileAccess.get_file_as_bytes(path)
	if bytes.size() > 262144 or bytes.is_empty():
		_fail("mod file size rejected")
		return
	# Hash exactly the bytes being parsed, closing a hash-before-read race.
	var hasher := HashingContext.new()
	hasher.start(HashingContext.HASH_SHA256)
	hasher.update(bytes)
	if hasher.finish().hex_encode() != expected_sha:
		_fail("mod bytes differ from approved digest")
		return
	var document = JSON.parse_string(bytes.get_string_from_utf8())
	if typeof(document) != TYPE_DICTIONARY or document.get("schema") != "deepbrew.behavior.v1":
		_fail("unsupported external mod schema")
		return
	for key in document.keys():
		if key not in ["schema", "name", "target", "behavior", "notes"]:
			_fail("unrecognized external mod field")
			return
	if typeof(document.get("behavior")) != TYPE_DICTIONARY:
		_fail("missing external mod behavior")
		return
	var behavior: Dictionary = document["behavior"]
	for key in behavior.keys():
		if key not in ["trigger", "effect", "duration_ms"]:
			_fail("unrecognized external behavior field")
			return
	if behavior.get("trigger", "") != "on_enter" or behavior.get("effect", "") not in ["closed", "open", "highlight"]:
		_fail("unknown external behavior instructions")
		return
	var duration = behavior.get("duration_ms")
	if (typeof(duration) != TYPE_INT and typeof(duration) != TYPE_FLOAT) or duration < 0 or duration > 60000 or duration != round(duration):
		_fail("invalid external behavior duration")
		return
	var world: Node3D = load("res://scenes/door_world.tscn").instantiate()
	root.add_child(world)
	await process_frame
	world.set_mod(document)
	world.player.global_position = Vector3(0, 0.9, 0)
	for i in range(5):
		await physics_frame
	var observed: Dictionary = world.observed()
	observed["approved_sha256"] = expected_sha
	observed["accepted"] = observed["entry_events"] == 1 and observed["state"] == behavior["effect"]
	print("EXTERNAL_GAME_RESULT " + JSON.stringify(observed))
	world.queue_free()
	await process_frame
	quit(0 if observed["accepted"] else 6)


func _fail(reason: String) -> void:
	print("EXTERNAL_GAME_REJECTED " + reason)
	quit(5)
