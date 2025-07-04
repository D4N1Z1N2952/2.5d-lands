from direct.showbase.ShowBase import ShowBase
from panda3d.core import CollisionTraverser, CollisionHandlerQueue, CollisionRay, CollisionNode, BitMask32, Point3, Vec3
from .player import Player # Relative import
from .block import Block  # Relative import
import math # For rounding positions
import json
import os

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Set up a simple light
        self.setup_lights()

        # Set up the camera - mouse will be enabled for picking
        # self.disableMouse() # We need mouse for picking, but default controls are not ideal
        self.camLens.setFov(90) # Wider FOV
        self.camLens.setNear(0.1) # Closer near plane for picking

        # Initialize collision system
        self.cTrav = CollisionTraverser("main_traverser")
        # self.cTrav.showCollisions(self.render) # For debugging collisions

        # Create the player
        self.player = Player(self)

        # World state
        self.blocks = {} # Dictionary to store blocks, mapping position tuple to Block instance

        # Mouse picking setup
        self.picker_ray = CollisionRay()
        picker_node = CollisionNode('mouse_ray_cnode')
        picker_node.addSolid(self.picker_ray)
        picker_node.setFromCollideMask(BitMask32.allOff()) # Rays don't have a 'from' type / don't act as solid objects
        picker_node.setIntoCollideMask(BitMask32.bit(0))   # Ray collides with world objects (mask 0)
        self.picker_np = self.camera.attachNewNode(picker_node)
        self.picker_handler = CollisionHandlerQueue()
        self.cTrav.addCollider(self.picker_np, self.picker_handler)

        # Input for block manipulation
        self.accept("mouse1", self.handle_left_click)    # Break block
        self.accept("mouse3", self.handle_right_click)   # Place block

        # Current block type to place
        self.current_block_type_to_place = "stone" # Default to stone
        self.accept("1", self.set_block_type_to_place, ["stone"])
        self.accept("2", self.set_block_type_to_place, ["grass"])
        self.accept("3", self.set_block_type_to_place, ["checkerboard"]) # New procedural block
        self.accept("4", self.set_block_type_to_place, ["red_block"])    # New color block
        self.accept("5", self.set_block_type_to_place, ["blue_block"])   # New color block
        self.accept("0", self.set_block_type_to_place, ["green_block"])  # New color block (using 0 for variety)


        # Update camera to follow player (and allow mouse look)
        self.taskMgr.add(self.update_camera_and_mouse_look, "update_camera_and_mouse_look_task")

        # Load block textures once
        Block.load_block_textures(self.loader)

        # Generate the world or load from save
        self.default_save_filename = "world_save.json"
        if not self.load_world(self.default_save_filename): # Try to load default save
            print("No save file found or error loading. Generating new world.")
            self.generate_world(size_x=10, size_y=10, ground_height=0, grass_depth=1, stone_depth=2)

        # Accept keys for saving/loading
        self.accept("f5", self.save_world_default)
        self.accept("f6", self.load_world_default) # Changed from F9 to F6 to avoid potential browser conflicts if run in web plugin


    def save_world_default(self):
        self.save_world(self.default_save_filename)

    def load_world_default(self):
        self.load_world(self.default_save_filename)

    def save_world(self, filename="world_save.json"):
        print(f"Saving world to {filename}...")
        save_dir = "saves"
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            filepath = os.path.join(save_dir, filename)

            world_data_to_save = []
            for pos_tuple, block_instance in self.blocks.items():
                block_data = {
                    "x": pos_tuple[0],
                    "y": pos_tuple[1],
                    "z": pos_tuple[2],
                    "type": block_instance.block_type
                }
                world_data_to_save.append(block_data)

            with open(filepath, 'w') as f:
                json.dump(world_data_to_save, f, indent=4)
            print(f"World saved successfully to {filepath}")
            return True
        except IOError as e:
            print(f"Error saving world: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while saving: {e}")
            return False

    def load_world(self, filename="world_save.json"):
        print(f"Attempting to load world from {filename}...")
        save_dir = "saves"
        filepath = os.path.join(save_dir, filename)

        if not os.path.exists(filepath):
            print(f"Save file not found: {filepath}")
            return False

        try:
            # Clear existing world first
            # Make a copy of items to iterate over for safe deletion
            current_block_items = list(self.blocks.items())
            for pos_tuple, block_instance in current_block_items:
                # Directly call remove method of block, it should handle its collision node etc.
                block_instance.remove()
            self.blocks.clear() # Clear the dictionary

            with open(filepath, 'r') as f:
                loaded_data = json.load(f)

            if not isinstance(loaded_data, list):
                print("Error: Save file format is incorrect (should be a list of blocks).")
                return False

            for block_data in loaded_data:
                if not isinstance(block_data, dict):
                    print(f"Warning: Skipping invalid block data entry: {block_data}")
                    continue
                try:
                    pos = Point3(block_data["x"], block_data["y"], block_data["z"])
                    block_type = block_data["type"]
                    self.add_block(pos, block_type)
                except KeyError as e:
                    print(f"Warning: Skipping block with missing data field {e}: {block_data}")
                except Exception as e:
                    print(f"Warning: Error processing block data {block_data}: {e}")

            print(f"World loaded successfully from {filepath}")
            # Optional: Reset player position or handle gracefully
            # For now, player will just be where they were, potentially falling if blocks changed.
            # self.player.setPos(0,0,5) # Example: Reset player to a known safe spot
            return True
        except IOError as e:
            print(f"Error loading world (IOError): {e}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error decoding save file (JSONDecodeError): {e}. File might be corrupted.")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while loading: {e}")
            return False


    def generate_world(self, size_x, size_y, ground_height, grass_depth, stone_depth):
        print(f"Generating world: {size_x}x{size_y}, ground at Z={ground_height}")
        for x in range(-size_x // 2, size_x // 2):
            for y in range(-size_y // 2, size_y // 2):
                # Grass layer
                for d in range(grass_depth):
                    self.add_block(Point3(x, y, ground_height - d), "grass")
                # Stone layer underneath
                for d in range(grass_depth, grass_depth + stone_depth):
                    self.add_block(Point3(x, y, ground_height - d), "stone")

        # Ensure player starts on top of the generated world
        # Player's initial Z is 2, model_height_offset is 0.3. Feet at 1.7.
        # If ground_height is 0, this should be fine.
        # If ground_height changes, player start pos might need adjustment.
        # For now, player starts at (0,0,2) and should fall onto the ground_height=0 plane.


    def setup_lights(self):
        # Ambient Light
        from panda3d.core import AmbientLight
        ambient_light = AmbientLight('ambient_light')
        ambient_light.setColor((0.3, 0.3, 0.3, 1))
        self.ambient_light_node = self.render.attachNewNode(ambient_light)
        self.render.setLight(self.ambient_light_node)

        # Directional Light
        from panda3d.core import DirectionalLight
        directional_light = DirectionalLight('directional_light')
        directional_light.setColor((0.8, 0.8, 0.8, 1))
        directional_light.setShadowCaster(True, 512, 512)
        self.directional_light_node = self.render.attachNewNode(directional_light)
        self.directional_light_node.setHpr(0, -60, 0) # Direction of the light
        self.render.setLight(self.directional_light_node)
        self.render.setShaderAuto()

    def set_block_type_to_place(self, block_type):
        print(f"Selected block type: {block_type}")
        self.current_block_type_to_place = block_type

    def add_block(self, position, block_type):
        # Round position to nearest grid cell
        pos_tuple = (round(position.x), round(position.y), round(position.z))

        if pos_tuple not in self.blocks:
            print(f"Adding {block_type} block at {pos_tuple}")
            new_block = Block(self, Vec3(pos_tuple), block_type)
            new_block.reparentTo(self.render)
            self.blocks[pos_tuple] = new_block
            return new_block
        return None

    def remove_block(self, block_instance):
        if block_instance:
            pos_tuple = (round(block_instance.getX()), round(block_instance.getY()), round(block_instance.getZ()))
            print(f"Removing block at {pos_tuple}")
            if pos_tuple in self.blocks:
                self.blocks[pos_tuple].remove()
                del self.blocks[pos_tuple]

    def get_block_hit(self):
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            self.picker_ray.setFromLens(self.camNode, mpos.getX(), mpos.getY())

            self.cTrav.traverse(self.render) # Check collisions with render

            if self.picker_handler.getNumEntries() > 0:
                self.picker_handler.sortEntries() # Sort by distance
                entry = self.picker_handler.getEntry(0)
                picked_node_path = entry.getIntoNodePath()

                # Traverse up to find the parent 'Block' instance if it exists
                current_np = picked_node_path
                while current_np != self.render and current_np.getParent() != self.render:
                    if isinstance(current_np.node(), PandaNode) and "block-" in current_np.getName(): # Check if it's one of our blocks
                        # Find the Block instance associated with this NodePath
                        for block in self.blocks.values():
                            if block == current_np:
                                return block, entry.getSurfacePoint(self.render), entry.getSurfaceNormal(self.render)
                    current_np = current_np.getParent()
                # If the hit object is directly a block (e.g. no complex hierarchy within block.model)
                if isinstance(picked_node_path.node(), PandaNode) and "block-" in picked_node_path.getName():
                     for block in self.blocks.values():
                            if block == picked_node_path:
                                return block, entry.getSurfacePoint(self.render), entry.getSurfaceNormal(self.render)

        return None, None, None


    def handle_left_click(self): # Break block
        block_hit, hit_pos, hit_normal = self.get_block_hit()
        if block_hit:
            self.remove_block(block_hit)

    def handle_right_click(self): # Place block
        block_hit, hit_pos, hit_normal = self.get_block_hit()
        if hit_pos is not None and hit_normal is not None:
            # Calculate placement position: on the face of the hit block
            # Ensure the new block is snapped to the grid
            place_pos = hit_pos + hit_normal * 0.5 # Place adjacent to the hit surface

            # Snap to grid more reliably
            # The idea is to find the center of the block we'd be placing if we were inside the hit block's cell, then offset by normal
            if block_hit:
                target_block_center = block_hit.getPos()
                new_block_center_x = target_block_center.x + hit_normal.x
                new_block_center_y = target_block_center.y + hit_normal.y
                new_block_center_z = target_block_center.z + hit_normal.z
                final_place_pos = Point3(round(new_block_center_x), round(new_block_center_y), round(new_block_center_z))
            else: # Fallback if not hitting a block (e.g. placing on an imaginary plane)
                 final_place_pos = Point3(round(place_pos.x), round(place_pos.y), round(place_pos.z))

            # Prevent placing block inside player
            player_pos_rounded = Point3(round(self.player.getX()), round(self.player.getY()), round(self.player.getZ()))
            player_head_pos_rounded = Point3(round(self.player.getX()), round(self.player.getY()), round(self.player.getZ() + 1)) # Approx head

            if final_place_pos == player_pos_rounded or final_place_pos == player_head_pos_rounded:
                print("Cannot place block inside player.")
                return

            self.add_block(final_place_pos, self.current_block_type_to_place)


    def update_camera_and_mouse_look(self, task):
        # Basic first-person camera controls
        md = self.win.getPointer(0)
        x = md.getX()
        y = md.getY()

        if self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2):
            self.player.setH(self.player.getH() - (x - self.win.getXSize() // 2) * 0.1)
            self.camera.setP(self.camera.getP() - (y - self.win.getYSize() // 2) * 0.1)

            # Clamp camera pitch
            min_pitch = -85
            max_pitch = 85
            if self.camera.getP() < min_pitch:
                self.camera.setP(min_pitch)
            elif self.camera.getP() > max_pitch:
                self.camera.setP(max_pitch)

        # Camera follows player's position and orientation (H from player, P from camera itself)
        self.camera.setPos(self.player.getPos() + (0,0,0.5)) # Camera at player's eye level
        self.camera.setHpr(self.player.getH(), self.camera.getP(), 0) # Player H, Camera P, 0 Roll

        # Update player's orientation for movement if needed (player model faces where camera looks horizontally)
        # This means player model will rotate with mouse H.
        # If you want player model to be independent of camera H, then don't do this.
        # self.player.model.setHpr(self.camera.getH(), 0, 0) # Or self.player.getH() if player has own rotation logic

        # Run collision traversal for player physics (and picker, though picker also traverses on click)
        self.cTrav.traverse(self.render)

        return task.cont


app = MyApp()
app.run()
