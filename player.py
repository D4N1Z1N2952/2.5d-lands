from panda3d.core import NodePath, PandaNode, Point3, Vec3
from panda3d.core import CollisionSphere, CollisionNode, CollisionHandlerQueue, CollisionRay, CollisionHandlerPusher, BitMask32
from direct.showbase.ShowBaseGlobal import globalClock

class Player(NodePath):
    def __init__(self, base):
        self.base = base
        NodePath.__init__(self, PandaNode("player"))
        self.reparentTo(self.base.render) # Player NodePath is now child of render

        # Player model (simple sphere for now)
        self.model = self.base.loader.loadModel("models/misc/sphere")
        self.model.reparentTo(self) # Model is child of Player NodePath
        self.model.setScale(0.3)
        self.model_height_offset = 0.3 # Radius of the sphere, for ground check
        self.setPos(0, 0, 2) # Initial position, higher to fall onto blocks

        # Movement variables
        self.speed = 5.0
        self.jump_force = 7.0 # Adjusted jump force
        self.gravity = -19.6
        self.vertical_velocity = 0.0
        self.is_jumping = False
        self.on_ground = False # Start in the air

        # Input state
        self.key_map = {
            "forward": False, "backward": False, "left": False, "right": False, "jump": False
        }

        # Setup input
        self.base.accept("w", self.set_key, ["forward", True])
        self.base.accept("w-up", self.set_key, ["forward", False])
        self.base.accept("s", self.set_key, ["backward", True])
        self.base.accept("s-up", self.set_key, ["backward", False])
        self.base.accept("a", self.set_key, ["left", True])
        self.base.accept("a-up", self.set_key, ["left", False])
        self.base.accept("d", self.set_key, ["right", True])
        self.base.accept("d-up", self.set_key, ["right", False])
        self.base.accept("space", self.set_key, ["jump", True])
        # "space-up" is not strictly needed for this jump logic but good practice
        self.base.accept("space-up", self.set_key, ["jump", False])

        # Collision setup for ground detection (ray from player center downwards)
        self.ground_ray = CollisionRay()
        # Ray origin is at player's feet (center - offset)
        self.ground_ray.setOrigin(0, 0, -self.model_height_offset + 0.05) # Start ray slightly inside the model bottom
        self.ground_ray.setDirection(0, 0, -1) # Shoots downwards

        self.ground_col_node = CollisionNode('player_ground_ray_cnode')
        self.ground_col_node.addSolid(self.ground_ray)
        self.ground_col_node.setFromCollideMask(BitMask32.allOff()) # Ray should not be solid itself
        self.ground_col_node.setIntoCollideMask(BitMask32.bit(0))   # Ray collides with world objects (mask 0)
        self.ground_col_np = self.attachNewNode(self.ground_col_node) # Attach to player NodePath
        # self.ground_col_np.show() # For debugging the ray

        self.ground_handler = CollisionHandlerQueue()
        # Add player's ground ray to the main traverser in MyApp
        self.base.cTrav.addCollider(self.ground_col_np, self.ground_handler)

        # Collision setup for player body (sphere) to prevent walking through blocks
        player_col_solid = CollisionSphere(0, 0, 0, self.model_height_offset * 1.1) # Slightly larger than visual model
        self.player_col_node = CollisionNode('player_collider_cnode')
        self.player_col_node.addSolid(player_col_solid)
        self.player_col_node.setFromCollideMask(BitMask32.bit(1)) # Player collision mask
        self.player_col_node.setIntoCollideMask(BitMask32.bit(0))   # Collide with world
        self.player_col_np = self.attachNewNode(self.player_col_node)
        # self.player_col_np.show()

        self.player_pusher = CollisionHandlerPusher()
        self.player_pusher.addCollider(self.player_col_np, self) # Pusher will move 'self' (the Player NodePath)
        self.base.cTrav.addCollider(self.player_col_np, self.player_pusher)


        # Task for player update
        self.base.taskMgr.add(self.update_player, "update_player_task")

    def set_key(self, key, value):
        self.key_map[key] = value
        if key == "jump" and value == False: # Handle jump release if needed for future mechanics
            pass


    def update_player(self, task):
        dt = globalClock.getDt()
        current_pos = self.getPos()

        # --- Ground Detection ---
        self.on_ground = False # Assume not on ground until ray confirms
        # self.base.cTrav.traverse(self.base.render) # Traversal is done in main loop or by MyApp's traverser

        # Check ground ray collisions
        if self.ground_handler.getNumEntries() > 0:
            self.ground_handler.sortEntries() # Closest hit first
            ground_contact = self.ground_handler.getEntry(0)
            hit_pos = ground_contact.getSurfacePoint(self.base.render)
            # Distance from player's origin (feet) to the ground contact point
            # Ray origin is at self.model_height_offset from player NodePath's origin
            # So, player's feet are at current_pos.z - self.model_height_offset
            # Effective ray length to consider is short, e.g., 0.2 units down from feet
            # Player's Z position is its center. Feet are at Z - model_height_offset.
            # Ray starts at Z - model_height_offset + 0.05 and goes down.
            # If hit_pos.z is very close to (current_pos.z - self.model_height_offset), we are on ground.

            # Distance from player's feet (origin of ray) to the hit point
            # The ray origin is self.ground_ray.getOrigin(), relative to self (Player NP)
            # So, world origin of ray is self.getPos() + self.ground_ray.getOrigin()
            # For simplicity, check if the hit is within a small tolerance below the player's model bottom

            # Distance from player's origin to ground. Player origin is its center.
            # Player feet are at current_pos.z - self.model_height_offset.
            # If hit_pos.z is close to this, we are on ground.
            # A small tolerance, e.g., if player's feet are within 0.1 of the hit surface.
            if hit_pos.getZ() > current_pos.getZ() - self.model_height_offset - 0.1: # If hit is close below feet
                self.on_ground = True
                # Snap player to ground if they are slightly above or sunk in
                self.setZ(hit_pos.getZ() + self.model_height_offset)
                self.vertical_velocity = 0
                self.is_jumping = False


        # --- Apply Gravity ---
        if not self.on_ground:
            self.vertical_velocity += self.gravity * dt

        # Update vertical position
        delta_z = self.vertical_velocity * dt
        self.setZ(self.getZ() + delta_z)

        # --- Jumping ---
        if self.key_map["jump"] and self.on_ground and not self.is_jumping:
            self.vertical_velocity = self.jump_force
            self.is_jumping = True
            self.on_ground = False # Player leaves ground

        # --- Horizontal Movement ---
        # Movement is relative to the player's current heading (which is controlled by mouse in main.py)
        move_direction = Vec3(0, 0, 0)
        if self.key_map["forward"]:
            move_direction.setY(move_direction.getY() + self.speed * dt)
        if self.key_map["backward"]:
            move_direction.setY(move_direction.getY() - self.speed * dt)
        if self.key_map["left"]:
            move_direction.setX(move_direction.getX() - self.speed * dt)
        if self.key_map["right"]:
            move_direction.setX(move_direction.getX() + self.speed * dt)

        # Transform movement vector from player's local space to world space
        # Player's rotation (H) is set by mouse in main.py
        # We want to move along the player's local X and Y axes.
        # self.getQuat().getForward() gives world-space forward vector
        # self.getQuat().getRight() gives world-space right vector

        # Simpler: move relative to self, then Panda3D handles world transform
        # self.setPos(self, move_direction) works if self (Player NP) is rotated.
        # The Player NodePath itself (self) is rotated by main.py's camera update.

        # We need to apply the movement considering the player's rotation (H value)
        # The player's H (heading) is set in main.py's update_camera_and_mouse_look
        # So, self.getH() is the current heading.

        # Calculate movement in world space based on player's heading
        current_h_rad = self.getH() * (3.14159 / 180.0)
        cos_h = math.cos(current_h_rad)
        sin_h = math.sin(current_h_rad)

        world_move_x = move_direction.getX() * cos_h - move_direction.getY() * sin_h
        world_move_y = move_direction.getX() * sin_h + move_direction.getY() * cos_h

        # Update position based on world movement vector
        new_x = current_pos.getX() + world_move_x
        new_y = current_pos.getY() + world_move_y
        self.setX(new_x)
        self.setY(new_y)

        # After movement, collision pusher will handle block collisions.
        # The ground ray collision will re-adjust Z if player falls onto a block.

        return task.cont

    def cleanup(self):
        self.base.taskMgr.remove("update_player_task")
        self.base.ignore("w")
        self.base.ignore("w-up")
        self.base.ignore("s")
        self.base.ignore("s-up")
        self.base.ignore("a")
        self.base.ignore("a-up")
        self.base.ignore("d")
        self.base.ignore("d-up")
        self.base.ignore("space")
        self.base.ignore("space-up")

        if self.ground_col_np:
            self.base.cTrav.removeCollider(self.ground_col_np)
            self.ground_col_np.removeNode()
        if self.player_col_np:
            self.base.cTrav.removeCollider(self.player_col_np) # Pusher handles its own removal from traverser if needed
            self.player_col_np.removeNode()

        self.model.removeNode()
        self.removeNode()
import math # Ensure math is imported if not already at top
