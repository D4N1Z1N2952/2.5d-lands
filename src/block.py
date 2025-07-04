from panda3d.core import NodePath, PandaNode, Point3, Texture, TextureStage
from panda3d.core import TexturePool, TransparencyAttrib # TransparencyAttrib might not be needed now
from panda3d.core import Vec3

class Block(NodePath):
    # Pre-load textures to avoid loading them for every block instance
    textures = {}

    @classmethod
    def load_block_textures(cls, loader):
        # User will need to create a 'textures' folder and place these files in it.
        # For grass, we'll use grass_side for all faces for simplicity with the default box model.
        # A more advanced setup would use different textures for top/bottom/sides.
        try:
            cls.textures["grass"] = loader.loadTexture("assets/textures/grass_side.png")
            cls.textures["grass"].setMagfilter(Texture.FTNearest)
            cls.textures["grass"].setMinfilter(Texture.FTNearestMipmapNearest)
        except Exception as e:
            print(f"Warning: Could not load grass texture from assets/textures/grass_side.png: {e}. Using fallback color.")
            cls.textures["grass"] = None

        try:
            cls.textures["stone"] = loader.loadTexture("assets/textures/stone.png")
            cls.textures["stone"].setMagfilter(Texture.FTNearest)
            cls.textures["stone"].setMinfilter(Texture.FTNearestMipmapNearest)
        except Exception as e:
            print(f"Warning: Could not load stone texture from assets/textures/stone.png: {e}. Using fallback color.")
            cls.textures["stone"] = None

        # Example for a more complex grass block if using a model with multiple texture stages
        # or a custom shader:
        # cls.textures["grass_top"] = loader.loadTexture("assets/textures/grass_top.png")
        # cls.textures["dirt"] = loader.loadTexture("assets/textures/dirt.png")


    def __init__(self, base, position=Vec3(0,0,0), block_type="stone"):
        NodePath.__init__(self, PandaNode(f"block-{block_type}-{position}"))
        self.base = base
        self.block_type = block_type

        if not Block.textures: # Ensure textures are loaded once
            Block.load_block_textures(self.base.loader)

        self.model = self.base.loader.loadModel("models/box")
        self.model.reparentTo(self)

        self.setPos(position)
        self.set_texture(block_type)

        # Collision setup for the block
        # This allows the player and mouse ray to interact with it.
        from panda3d.core import CollisionNode, CollisionBox, BitMask32
        cNode = CollisionNode(self.getName() + "_cnode")
        # Assuming block is 1x1x1 centered at its origin
        cNode.addSolid(CollisionBox(Point3(-0.5, -0.5, -0.5), Point3(0.5, 0.5, 0.5)))
        cNode.setIntoCollideMask(BitMask32.bit(0)) # World collision mask
        cNode.setFromCollideMask(BitMask32.allOff())
        self.collision_np = self.attachNewNode(cNode)
        # self.collision_np.show() # For debugging

    def set_texture(self, block_type):
        tex = Block.textures.get(block_type)
        if tex:
            self.model.setTexture(tex, 1)
            self.model.setColorOff() # Remove fallback color if texture is applied
        else:
            # Fallback to color if texture is missing
            if block_type == "grass":
                self.model.setColor(0, 0.5, 0, 1) # Green
            elif block_type == "stone":
                self.model.setColor(0.5, 0.5, 0.5, 1) # Grey
            else:
                self.model.setColor(1,1,1,1) # White for unknown

    def remove(self):
        # Clean up the block
        if self.collision_np:
            self.collision_np.removeNode()
        if self.model:
            self.model.removeNode()
        self.removeNode()

# Example usage (will be managed by a World class or similar later)
# Note: If running this script standalone (python src/block.py),
# texture loading might not work as expected because Block.load_block_textures()
# relies on paths relative to where the main application (ShowBase instance)
# is initialized, typically the project root. The main game (src/main.py)
# handles this correctly. This example is primarily for isolated Block class testing.
if __name__ == '__main__':
    from direct.showbase.ShowBase import ShowBase
    app = ShowBase()

    # To make textures load in this standalone example, you might need to explicitly call:
    # Block.load_block_textures(app.loader)
    # And ensure your current working directory is the project root, or adjust paths.
    # For simplicity, this example will likely show fallback colors if run directly.

    # Create some blocks
    b1 = Block(app, position=Vec3(0,0,0), block_type="grass")
    b1.reparentTo(app.render)

    b2 = Block(app, position=Vec3(1,0,0), block_type="stone")
    b2.reparentTo(app.render)

    b3 = Block(app, position=Vec3(0,1,0), block_type="grass")
    b3.reparentTo(app.render)

    app.camera.setPos(5, -5, 5)
    app.camera.lookAt(0,0,0)
    app.run()
