# pfa-week04
I used Claude Code to create a side-scrolling platformer using Python and Pygame. You play as "Pop Cat": jump over purple blocks, land on yellow ones, and collect gold coins—all while surviving as long as possible as the game speed steadily increases. The more coins you collect, the larger the cat appears on the game-over screen.

## How to run it
You need Python and a terminal. Then copy the lines below into a terminal.

Windows(PowerShell):

    cd ~\pygame-class
    .\.venv\Scripts\Activate.ps1
    pip install pygame
    python ball_game\main.py

Mac (Terminal):

    cd ~/pygame-class
    source .venv/bin/activate
    pip install pygame-ce
    python ball_game/main.py

### Controls

| Key           | Action                                            |
| ------------- | ------------------------------------------------- |
| ← → or A / D  | move                                              |
| Space, ↑ or W | jump                                              |
| Mouse         | click Restart / Quit Game on the game over screen |
| Esc           | quit                                              |

## What I Made Better
1. Added yellow platforms and purple obstacles.
2. Made the game speed increase over time.
3. Added coins that the player can collect.
4. Changed the ball to a Pop Cat image.
5. Added a game-over screen with the final time and coins.
6. Made the image on the game-over screen grow bigger based on the number of coins collected.
7. Added a changing background color. The background changes based on how long the player survives.

## How it works
1. This function checks if player touches a coin. When the player collects a coin, the coin disappears and the coin count goes up by one.

       def collect_coins(game):

2. This function is made by hand. It uses "if, elif, else"s to change the background color based on how long the player survives. The color changes every 10 seconds, so the game feels different as time goes on.

       def background_color(seconds):

3. This function makes the player jump. It checks whether the player is standing on the ground or a platform. If true, the player can jump.
   
       def jump(ball):


# video link
https://drive.google.com/file/d/1FujMqyXa4g1DjGHYRcdSoJIb-a-1Nebz/view?usp=sharing
