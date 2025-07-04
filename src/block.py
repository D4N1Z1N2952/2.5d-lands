from panda3d.core import NodePath, PandaNode, Point3, Texture, TextureStage
from panda3d.core import TexturePool, TransparencyAttrib # TransparencyAttrib might not be needed now
from panda3d.core import Vec3

class Block(NodePath):
    # Pre-load textures to avoid loading them for every block instance
    textures = {}

    @classmethod
    def generate_checkerboard_texture(cls, name="checkerboard", size=32, c1=(0.2,0.2,0.2,1), c2=(0.8,0.8,0.8,1)):
        """Generates a Texture object with a checkerboard pattern."""
        tex = Texture(name)
        tex.setup_2d_texture(size, size, Texture.T_unsigned_byte, Texture.F_rgba)

        img = tex.modify_ram_image() # Returns a PNMImage if Panda was built with libpng/tiff etc.
                                     # Or a simple memory view / PTA_uchar if not.
                                     # We'll assume PNMImage for set_xel_val, otherwise direct memory manipulation is needed.

        # Check if img is a PNMImage or a memory view
        is_pnm_image = hasattr(img, "set_xel_val")

        for y in range(size):
            for x in range(size):
                if (x // (size // 4)) % 2 == (y // (size // 4)) % 2: # Creates larger checkers
                    col = c1
                else:
                    col = c2

                if is_pnm_image:
                    # PNMImage expects color components from 0 to 255 for set_xel_val with RGBA
                    img.set_xel_val(x, y, int(col[0]*255), int(col[1]*255), int(col[2]*255), int(col[3]*255))
                else: # Direct memory manipulation (more complex, assumes PTA_uchar for F_rgba)
                    # This part requires knowing the exact memory layout (e.g. PTA_uchar)
                    # For RGBA, 4 bytes per pixel. img is a memoryview to a flat array.
                    # index = (y * size + x) * 4
                    # img[index + 0] = int(col[0] * 255)
                    # img[index + 1] = int(col[1] * 255)
                    # img[index + 2] = int(col[2] * 255)
                    # img[index + 3] = int(col[3] * 255)
                    # For simplicity, if not PNMImage, we might just skip or log a warning for this example.
                    # This example will primarily work if PNMImage is available.
                    if x == 0 and y == 0: # Print warning only once
                        print("Warning: PNMImage not available for procedural texture generation, checkerboard might not appear correctly.")
                        print("Consider building Panda3D with libpng/tiff support for full PNMImage features.")


        tex.setMagfilter(Texture.FTNearest)
        tex.setMinfilter(Texture.FTNearestMipmapNearest)
        return tex

    @classmethod
    def load_block_textures(cls, loader):
        # Load image-based textures
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

        # Load/Generate procedural textures
        try:
            cls.textures["checkerboard"] = cls.generate_checkerboard_texture(name="proc_checkerboard", size=32, c1=(0.1,0.1,0.1,1), c2=(0.9,0.9,0.9,1))
            print("Generated checkerboard texture.")
        except Exception as e:
            print(f"Error generating checkerboard texture: {e}")
            cls.textures["checkerboard"] = None

        # Example for a more complex grass block if using a model with multiple texture stages
        # or a custom shader:
        # cls.textures["grass_top"] = loader.loadTexture("assets/textures/grass_top.png")
        # cls.textures["dirt"] = loader.loadTexture("assets/textures/dirt.png")


    def __init__(self, base, position=Vec3(0,0,0), block_type="stone"):
        NodePath.__init__(self, PandaNode(f"block-{block_type}-{position}")) # Name the NodePath itself for easier debugging
        self.base = base
        self.block_type = block_type

        # Ensure textures (both image-based and procedural) are loaded/generated once.
        # This is typically called from MyApp.__init__ before any blocks are made.
        # If Block.textures is empty, it implies it's the first block being created.
        if not Block.textures:
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

    # Define solid colors for specific block types
    solid_colors = {
        "red_block": (1, 0, 0, 1),
        "blue_block": (0, 0, 1, 1),
        "green_block": (0,1,0,1) # A different green from grass fallback
    }

    def set_texture(self, block_type):
        self.model.clearTexture() # Clear any previous texture
        self.model.setColorOff()  # Reset color scale / flat color initially

        if block_type in Block.solid_colors:
            self.model.setColor(Block.solid_colors[block_type])
        else:
            tex = Block.textures.get(block_type)
            if tex:
                self.model.setTexture(tex, 1)
                # setColorOff already called, so model won't be tinted unless we want it to
            else:
                # Fallback to default colors if texture is missing and not a defined solid_color type
                if block_type == "grass":
                    self.model.setColor(0, 0.5, 0, 1) # Fallback Green for grass
                elif block_type == "stone":
                    self.model.setColor(0.5, 0.5, 0.5, 1) # Fallback Grey for stone
                else:
                    self.model.setColor(0.8, 0.8, 0.8, 1) # Default fallback for unknown types

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
