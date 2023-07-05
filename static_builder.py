# The "Hummy" Algorithm

from displaylib.math import *
import random
import math


workers: int = 24
iterations: int = 8
position_advance_chance = 70
direction_change_chance = 50
aoe_eat_chance = 10

randomize = True

if randomize:
    workers = random.randint(4, 32)
    iterations = random.randint(4, 12)
    position_advance_chance = random.randint(50, 100)
    direction_change_chance = random.randint(0, 100)
    aoe_eat_chance = random.randint(0, 100)

INITIAL_TOLERANCE = 300
WORLD_SIZE = Vec2(
    32,
    16
)
HALF_WORLD_SIZE = WORLD_SIZE // 2
SPACE = " "
PATH = "."
WALL = "#"


class Eater:
    def __init__(self, position: Vec2, direction: Vec2) -> None:
        self.position = position
        self.direction = direction


def get_neighbours(world: list[list[str]], location: Vec2) -> list[tuple[Vec2, str]]:
    positions = map(lambda position: HALF_WORLD_SIZE + location + position, (Vec2i(x, y) for x in range(-1, 2) for y in range(-1, 2)))
    return [(position, world[position.y][position.x]) for position in positions]

def generate_map() -> list[list[str]] | None:
    try:
        eaters: list[Eater] = [
        Eater(position=Vec2(0, 0),
            direction=Vec2(random.randint(-1, 1),
                            random.randint(-1, 1)))
        for _ in range(workers)
        ]
        world_map: list[list[str]] = [
            list(SPACE * WORLD_SIZE.x) for _ in range(WORLD_SIZE.y)
        ]
        # make start point painted
        for eater in eaters:
            location = HALF_WORLD_SIZE + eater.position
            if world_map[location.y][location.x] == SPACE:
                world_map[location.y][location.x] = PATH

        for _ in range(iterations):
            for eater in eaters:
                # move them
                if random.randint(1, 100) >= 100 - position_advance_chance:
                    eater.position += eater.direction
                if random.randint(1, 100) >= 100 - direction_change_chance:
                    rotation = 45 # deg
                    if random.randint(0, 1):
                        rotation *= -1
                    eater.direction = eater.direction.rotated(math.radians(rotation))
                    eater.direction.x = round(eater.direction.x)
                    eater.direction.y = round(eater.direction.y)

                # make them eat map
                if random.randint(1, 100) >= 100 - aoe_eat_chance:
                    for location, char in get_neighbours(world_map, eater.position):
                        if char == PATH:
                            continue
                        elif char == SPACE:
                            world_map[location.y][location.x] = PATH
                location = HALF_WORLD_SIZE + eater.position
                if world_map[location.y][location.x] == SPACE:
                    world_map[location.y][location.x] = PATH
        return world_map
    except IndexError:
        return None

if __name__ == "__main__":
    world_map = generate_map()
    fails = 0
    tolerance = INITIAL_TOLERANCE
    while world_map is None:
        print("[Info] Regenerating", f"({fails})")
        world_map = generate_map()
        fails += 1
        tolerance -= 1
        if not tolerance:
            print(f"[Info] Decreased iterations: {iterations} -> {iterations -1}")
            iterations -= 1
            tolerance = INITIAL_TOLERANCE
    # display map and used parameters
    print("=" * WORLD_SIZE.x)
    print("Area:   ", f"{WORLD_SIZE.x}x{WORLD_SIZE.y}")
    print("Workers:", workers)
    print("Cycles: ", iterations)
    print("Energy: ", f"{position_advance_chance}%")
    print("Turning:", f"{direction_change_chance}%")
    print("Hunger: ", f"{aoe_eat_chance}%")
    print("=" * WORLD_SIZE.x)
    for line in world_map:
        print("".join(line))
    print("=" * WORLD_SIZE.x)

    # save map
    with open("./map.txt", "w") as f:
        for line in world_map[:-1]:
            f.write("".join(line).replace(SPACE, WALL).replace(PATH, SPACE) + "\n")
        f.write("".join(world_map[-1]).replace(SPACE, WALL).replace(PATH, SPACE))
