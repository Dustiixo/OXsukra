extends SceneTree
## Automated native-headless proof of navigation on an exported, verified IXO snapshot.


func _initialize() -> void:
    call_deferred("_run")


func _fail(reason: String) -> void:
    printerr("OCEAN_SMOKE_FAIL: " + reason)
    quit(1)


func _run() -> void:
    var scene = load("res://scenes/ocean.tscn").instantiate()
    root.add_child(scene)
    await process_frame
    if scene.snapshot.is_empty():
        _fail("snapshot did not load")
        return
    if scene.objects.size() != 7:
        _fail("expected two native projects and five native entries")
        return
    if scene.controller_armed:
        _fail("controller must remain in standby")
        return
    var id: String = str(scene.snapshot["entries"][0]["id"])
    if not scene.objects.has(id):
        _fail("native entry identity not present in spatial index")
        return
    # Exercise the actual reticle-selection logic, not only a manually set ID.
    var point: Vector3 = scene.spheres[id].global_position
    scene.rig.position = point + Vector3(0, 0, 4)
    scene.rig.look_at(point, Vector3.UP)
    scene.selected_id = scene._aimed_object()
    if scene.selected_id != id:
        _fail("camera reticle did not select the expected real IXO record")
        return
    var pose: Transform3D = scene.rig.transform
    scene._enter_object()
    if scene.current_detail != id or scene.breadcrumbs.size() != 1:
        _fail("enter did not open the real IXO entry with a breadcrumb")
        return
    if not scene.ui_detail_text.text.contains(str(scene.objects[id]["source_sha256"])):
        _fail("entry detail did not preserve original source SHA-256")
        return
    scene._go_back()
    if scene.current_detail != "" or scene.breadcrumbs.size() != 0:
        _fail("B/back did not unwind the navigation path")
        return
    if not scene.rig.transform.is_equal_approx(pose):
        _fail("B/back did not restore the exact prior swim pose")
        return
    if scene.visual_links.size() == 0:
        _fail("verified approved link absent from 3D scene")
        return
    scene._toggle_sonar()
    if not scene.visual_links[0].visible:
        _fail("sonar did not expose an approved relationship")
        return
    scene._overview()
    if scene.breadcrumbs.size() != 1:
        _fail("God's Eye View did not save the prior pose")
        return
    scene._go_back()
    if not scene.rig.transform.is_equal_approx(pose):
        _fail("overview return did not restore pose")
        return
    scene._save_breadcrumbs()
    if not FileAccess.file_exists("user://ocean_navigation_state.json"):
        _fail("restart breadcrumb record was not persisted")
        return
    print("OCEAN_SMOKE_PASS native_objects=7 selected_original_hash=true breadcrumb_return=true sonar=true resume=true")
    quit(0)
