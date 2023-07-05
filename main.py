# The "Hummy" Algorithm visualized using DisplayLib

from displaylib import *
import random
import math
import keyboard


randomize: bool = False

area:   Vec2 = Vec2(32, 16)
workers: int = 24
cycles:  int = 8
energy:  int = 70
turning: int = 50
hunger:  int = 10

half_area: Vec2 = area // 2

if randomize:
    workers = random.randint(4, 32)
    cycles = random.randint(4, 12)
    energy = random.randint(50, 100)
    turning = random.randint(0, 100)
    hunger = random.randint(0, 100)

INITIAL_TOLERANCE: int = 5
AIR:  str = " "
PATH: str = "."
WALL: str = "#"


@pull("direction")
class Eater(Sprite): # data structure
    texture=[["%"]]
    def __init__(self, parent=None, x: int = 0, y: int = 0, direction: Vec2 = Vec2(0, 0), z_index: int = 0) -> None:
        super().__init__(parent, x=x, y=y, z_index=z_index)
        self.direction = direction

class WorldMap(Sprite): ...


def get_neighbours(world_map: WorldMap, location: Vec2) -> list[tuple[Vec2, str]]:
    positions = map(lambda position: location + position - world_map.position,
                    (Vec2i(x, y) for x in range(-1, 2) for y in range(-1, 2)))
    return [(position, world_map.texture[position.y][position.x]) for position in positions]


def save_map(world_map: WorldMap) -> None:
    with open("./map2.txt", "w") as f:
        for line in world_map.texture[:-1]:
            f.write("".join(line).replace(AIR, WALL).replace(PATH, AIR) + "\n")
        f.write("".join(world_map.texture[-1]).replace(AIR, WALL).replace(PATH, AIR))


class App(Engine):
    def _on_start(self) -> None:
        self.screen.width = area.x
        self.screen.height = area.y + 3 + 7 + 1
        self.frame_top = Sprite(texture=[list("="*self.screen.width)],       y=0)
        self.label_tolerance = Label(text=f"TOLERANCE: {INITIAL_TOLERANCE}", y=1)
        self.label_area = Label(text=f"Area:    {area.x}x{area.y}",          y=2)
        self.label_workers = Label(text=f"Workers: {workers}",               y=3)
        self.label_cycles = Label(text=f"Cycles:  {cycles}it",               y=4)
        self.label_energy = Label(text=f"Energy:  {energy}%",                y=5)
        self.label_turning = Label(text=f"Turning: {turning}%",              y=6)
        self.label_hunger = Label(text=f"Hunger:  {hunger}%",                y=7)
        self.frame_middle = Sprite(texture=[list("="*self.screen.width)],    y=8)
        self.frame_bottom = Sprite(texture=[list("="*self.screen.width)],    y=10+area.y)
        self.world_map = None
        self.world_generator = self.generate_world_map()
        self.is_regenerate_pressed = False
        self.is_randomize_pressed = False
        self.population_extinct = any(isinstance(node, Eater) for node in Node.nodes.values())
        self.fails = 0
        self.memory_map = None
    
    @staticmethod
    def generate_world_map():
        world_map = WorldMap(
            y=3+7,
            texture=[
                list(AIR * area.x)
                for _ in range(area.y)
            ])
        eaters: list[Eater] = [
            Eater(
                x=half_area.x,
                y=half_area.y+3+6,
                direction=Vec2(random.randint(-1, 1),
                               random.randint(-1, 1)))
            for _ in range(workers)
        ]
        try:
            # make start point painted
            for eater in eaters:
                location = eater.position - world_map.position
                if world_map.texture[location.y][location.x] == AIR:
                    world_map.texture[location.y][location.x] = PATH
            yield "OK"

            for _ in range(cycles):
                for eater in eaters:
                    # move them
                    if random.randint(1, 100) >= 100 - energy:
                        eater.position += eater.direction
                    if random.randint(1, 100) >= 100 - turning:
                        rotation = 45 # deg
                        if random.randint(0, 1):
                            rotation *= -1
                        eater.direction = eater.direction.rotated(math.radians(rotation))
                        eater.direction.x = round(eater.direction.x)
                        eater.direction.y = round(eater.direction.y)
                    yield "OK"

                    # eat where eater moved
                    location = eater.position - world_map.position
                    if world_map.texture[location.y][location.x] == AIR:
                        world_map.texture[location.y][location.x] = PATH
                    # make them eat map
                    if random.randint(1, 100) >= 100 - hunger:
                        for location, char in get_neighbours(world_map, eater.position):
                            if char == PATH:
                                continue
                            elif char == AIR:
                                world_map.texture[location.y][location.x] = PATH
                    yield "OK"
            eaters.clear()
            del eaters
            yield world_map
        except IndexError:
            world_map.queue_free()
            for eater in eaters:
                eater.queue_free()
            eaters.clear()
            del world_map
            del eaters
            yield "FAILED"
    
    def rebuild(self) -> None:
        self.world_map = None
        self.world_generator = self.generate_world_map()
        self.population_extinct = False
        for node in Node.nodes.values():
            if isinstance(node, (Eater, WorldMap)):
                node.queue_free()
        if randomize:
            global workers, cycles, energy, turning, hunger
            workers = random.randint(4, 32)
            cycles = random.randint(4, 12)
            energy = random.randint(50, 100)
            turning = random.randint(0, 100)
            hunger = random.randint(0, 100)
            self.label_area.text = f"Area:    {area.x}x{area.y}"
            self.label_workers.text = f"Workers: {workers}"
            self.label_cycles.text = f"Cycles:  {cycles}it"
            self.label_energy.text = f"Energy:  {energy}%"
            self.label_turning.text = f"Turning: {turning}%"
            self.label_hunger.text = f"Hunger:  {hunger}%"
    
    def _update(self, delta: float) -> None:
        if self.world_map is None:
            result = next(self.world_generator) # each step
            if result == "FAILED":
                self.fails += 1
                if self.fails == INITIAL_TOLERANCE:
                    global cycles
                    cycles -= 1
                    self.label_cycles.text = f"Cycles:  {cycles}it"
                self.rebuild()
            elif isinstance(result, WorldMap): # success
                self.world_map = result
                self.population_extinct = not any(isinstance(node, Eater) for node in Node.nodes.values())
            # else "OK"
        else:
            if not self.population_extinct:
                for node in Node.nodes.values():
                    if isinstance(node, Eater):
                        node.queue_free()
                        break
                self.population_extinct = not any(isinstance(node, Eater) for node in Node.nodes.values())
        
        if keyboard.is_pressed("space") and not self.is_regenerate_pressed:
            self.is_regenerate_pressed = True
            self.fails = 0
            self.rebuild()
        elif not keyboard.is_pressed("space") and self.is_regenerate_pressed:
            self.is_regenerate_pressed = False
        
        if keyboard.is_pressed(".") and not self.is_randomize_pressed:
            self.is_randomize_pressed = True
            self.fails = 0
            global randomize
            old_state = randomize
            randomize = True
            self.rebuild()
            randomize = old_state
        elif not keyboard.is_pressed(".") and self.is_randomize_pressed:
            self.is_randomize_pressed = False
        
        if keyboard.is_pressed("q"):
            self.is_running = False
        
        if keyboard.is_pressed(",") and self.world_map is not None and self.population_extinct:
            save_map(self.world_map)


if __name__ == "__main__":
    app = App(tps=60)
