extends Node3D

## An independently launched mini-game target, not DeepBrew's internal model.
## A real Godot physics Area3D detects an incoming CharacterBody3D.
## The external exported mod determines what physically happens to the door.

var setting: Dictionary = {}
var door: MeshInstance3D
var zone: Area3D
var player: CharacterBody3D
var state := "closed"
var entered_count := 0
var player_entered := false


func _ready() -> void:
	door = MeshInstance3D.new()
	door.name = "Door"
	var box := BoxMesh.new()
	box.size = Vector3(1.5, 2.8, 0.3)
	door.mesh = box
	door.position = Vector3(0, 1.4, 0)
	add_child(door)
	zone = Area3D.new()
	zone.name = "EntryZone"
	zone.monitoring = true
	var zone_shape := CollisionShape3D.new()
	var bounds := BoxShape3D.new()
	bounds.size = Vector3(4, 4, 4)
	zone_shape.shape = bounds
	zone.add_child(zone_shape)
	add_child(zone)
	player = CharacterBody3D.new()
	player.name = "Player"
	var player_shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.4
	capsule.height = 1.6
	player_shape.shape = capsule
	player.add_child(player_shape)
	player.position = Vector3(9, 0.9, 0)
	add_child(player)
	zone.body_entered.connect(_on_zone_entry)


func set_mod(document: Dictionary) -> void:
	setting = document.duplicate(true)
	state = "closed"
	entered_count = 0
	player_entered = false
	door.visible = true
	door.material_override = null


func _on_zone_entry(body: Node3D) -> void:
	if body != player or setting.is_empty():
		return
	entered_count += 1
	player_entered = true
	var behavior: Dictionary = setting["behavior"]
	state = str(behavior["effect"])
	if state == "open":
		door.visible = false
	elif state == "highlight":
		var material := StandardMaterial3D.new()
		material.albedo_color = Color("a3ff12")
		door.material_override = material


func observed() -> Dictionary:
	return {"state": state, "door_visible": door.visible,
		"entry_events": entered_count, "player_entered": player_entered,
		"duration_ms": int(setting.get("behavior", {}).get("duration_ms", -1)),
		"runtime": "external_godot_physics_area3d"}
