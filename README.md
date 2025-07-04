# Panda3D Minecraft-like Game Prototype

This project is a simple prototype of a Minecraft-like game built using Python and the Panda3D engine. It demonstrates basic 3D game mechanics including player movement, block placement/destruction, and a simple world.

## Features

*   **Player Control:**
    *   Move: WASD keys
    *   Jump: Spacebar
    *   Look: Mouse (first-person perspective)
*   **Block Interaction:**
    *   Break Block: Left Mouse Click
    *   Place Block: Right Mouse Click
    *   Select Block Type for Placing:
        *   '1': Stone (textured)
        *   '2': Grass (textured)
        *   '3': Checkerboard (procedural texture)
        *   '4': Red Block (solid color)
        *   '5': Blue Block (solid color)
        *   '0': Green Block (solid color)
    *   Save World: F5 (saves to `saves/world_save.json`)
    *   Load World: F6 (loads from `saves/world_save.json`)
*   **World:**
    *   Simple, flat generated world with grass and stone layers (if no save file is found).
    *   Basic collision detection and gravity.
*   **Texturing:**
    *   Blocks are textured (requires user to provide texture files).
    *   Fallback to solid colors if textures are not found.

## Project Structure

```
.
├── .gitattributes        # Manages line endings and file types for Git
├── .gitignore            # Specifies intentionally untracked files that Git should ignore
├── README.md             # This file
├── assets/               # Game assets
│   └── textures/         # Texture files (e.g., grass_side.png, stone.png)
└── src/                  # Source code
    ├── main.py           # Main application logic, Panda3D setup
    ├── player.py         # Player class (movement, physics, camera)
    └── block.py          # Block class (properties, texturing, interaction)
```

## Setup and Installation

### Prerequisites

*   **Python:** Version 3.7 or higher is recommended. You can download Python from [python.org](https://www.python.org/).
*   **Panda3D:** The core 3D engine.

### Installation Steps

1.  **Clone the repository (or download the source code):**
    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2.  **Run the Setup Script (Recommended):**
    Navigate to the root directory of the project in your terminal and run the setup script:
    ```bash
    python setup_game.py
    ```
    This script will:
    *   Check your Python version.
    *   Check if `pip` (Python package installer) is available.
    *   Attempt to install Panda3D if it's not already installed.
    Follow any instructions or messages provided by the script.

3.  **Manual Installation (if setup script fails or preferred):**
    *   **Install Panda3D:** If you have `pip`, you can install Panda3D by running:
        ```bash
        python -m pip install Panda3D
        ```
        For more detailed installation instructions or alternative methods, please refer to the [official Panda3D download page](https://www.panda3d.org/download/).

4.  **Place Texture Files:**
    *   Create the directory `assets/textures/` if it doesn't exist.
    *   You will need to provide your own texture images for the blocks. Place the following files in the `assets/textures/` directory:
        *   `grass_side.png` (used for all sides of grass blocks)
        *   `stone.png`
    *   If these files are not found, the blocks will appear as solid green (grass) or grey (stone). 16x16 pixel art textures are common for this style of game.

## How to Run

1.  Ensure you have completed the Setup and Installation steps, including installing Panda3D and placing the texture files.
2.  Navigate to the root directory of the project in your terminal.
3.  Run the main game file:
    ```bash
    python src/main.py
    ```
    *(Note: If your Python path is set up to include the `src` directory, or if you navigate into `src` and run `python main.py`, the imports should work. Running `python -m src.main` from the root directory is also a robust way if `src` is a package.)*

## Future Enhancements (Planned / Possible)

*   Installation script to automate dependency checks and installation.
*   Saving and loading game state (world data).
*   More diverse block types and textures.
*   Procedurally generated terrain.
*   Inventory system.
*   Crafting system.
*   Improved graphics and visual effects.

## Contributing

This is a small prototype. Contributions or suggestions are welcome! Please feel free to fork the repository, make changes, and open a pull request.

---

This README provides a basic overview. For more detailed information on Panda3D, please consult the [Panda3D Manual](https://docs.panda3d.org/1.10/python/index).
