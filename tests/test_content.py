#!/usr/bin/env python3
"""Asset, topology, invariants and content checks that do NOT claim engine execution."""
import json, re, struct, wave, unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]

class SourceAndContentTests(unittest.TestCase):
 def setUp(self):
  self.world=json.loads((ROOT/'data/world.json').read_text())
  self.recipes=json.loads((ROOT/'data/recipes.json').read_text())['recipes']
  self.game=(ROOT/'scripts/game.gd').read_text()
 def test_authoritative_godot_project_exists(self):
  self.assertTrue((ROOT/'project.godot').is_file())
  self.assertIn('res://scenes/game.tscn',(ROOT/'project.godot').read_text())
  self.assertIn('res://scripts/game.gd',(ROOT/'scenes/game.tscn').read_text())
 def test_world_cardinal_topology(self):
  regions=self.world['regions'];self.assertEqual(len(regions),16)
  self.assertEqual([x['id'] for x in regions if x['is_cardinal']],['WEST','NORTH','EAST','SOUTH'])
  for index,r in enumerate(regions):
   self.assertEqual(r['index'],index)
   self.assertEqual(r['x_start'],index*300)
   self.assertEqual(r['x_end'],(index+1)*300)
  self.assertEqual(self.world['width'],16*300)
 def test_unique_and_reachable_objects(self):
  objs=self.world['objects'];resources=self.world['resources'];enemies=self.world['enemies']
  ids=[x['id'] for x in objs+resources+enemies]
  self.assertEqual(len(ids),len(set(ids)))
  for r in objs+resources+enemies: self.assertTrue(0<=r['x']<self.world['width'])
  self.assertTrue(any(x['kind']=='npc' and x['x']<250 for x in objs))
  self.assertTrue(any(x['kind']=='workbench' and x['x']<250 for x in objs))
 def test_craft_quest_is_resource_feasible(self):
  recipe=next(x for x in self.recipes if x['id']=='signal_key')
  self.assertEqual(recipe['grants'],{'signal_key':1})
  self.assertGreaterEqual(sum(x['kind']=='shard' for x in self.world['resources'] if x['x']<1317),recipe['requires']['shard'])
  self.assertGreaterEqual(sum(x['kind']=='fiber' for x in self.world['resources'] if x['x']<1317),recipe['requires']['fiber'])
 def test_asset_sizes_and_transparency(self):
  atlas=Image.open(ROOT/'assets/player_atlas.png')
  self.assertEqual(atlas.size,(32*12,32*4))
  self.assertEqual(atlas.mode,'RGBA')
  self.assertLess(atlas.getpixel((0,0))[3],100)
  self.assertGreater(atlas.getpixel((16,16))[3],0)
  with Image.open(ROOT/'assets/world_atlas.png') as world_atlas:
   self.assertEqual(world_atlas.size,(32*10,32))
 def test_original_audio_is_real_pcm(self):
  with wave.open(str(ROOT/'assets/original_theme.wav')) as w:
   self.assertEqual(w.getframerate(),22050)
   self.assertGreater(w.getnframes(),100000)
   self.assertEqual(w.getnchannels(),1)
 def test_foreground_is_only_behavior(self):
  self.assertIn('func _update_player',self.game)
  self.assertIn('func _update_enemies',self.game)
  self.assertIn('func _release_grab',self.game)
  self.assertIn('func save_game',self.game)
  self.assertIn('func _draw_player',self.game)
  for prohibited in ['JavaScriptBridge','OS.execute(','DisplayServer.window_set_mouse_passthrough','DirAccess.open("C:','get_window_handle','Win32API']:
   self.assertNotIn(prohibited,self.game)
 def test_no_duplicate_function_declarations(self):
  names=re.findall(r'^func ([\w]+)\(',self.game,re.M)
  self.assertEqual(len(names),len(set(names)))
 def test_stable_content_files_json(self):
  for f in (ROOT/'data').glob('*.json'): json.loads(f.read_text())
 def test_save_temp_backup_and_schema_in_source(self):
  for token in ['save_temp','save_backup','"schema": 1','DirAccess.rename_absolute','FileAccess.get_file_as_string']:
   self.assertIn(token,self.game)

if __name__=='__main__':unittest.main(verbosity=2)
