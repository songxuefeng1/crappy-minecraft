from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from l3dBackfront import JsonFileHandler
import os
import time
from random import choice, uniform

app = Ursina()
Sky()   
player = FirstPersonController(y=2, gravity=0.8)

class Block():
    def __init__(self, position=(0, 0, 0), blockId=1):
        self.blockId = blockId
        texture_set_info = JsonFileHandler('textures/textureSets.json').get(str(blockId))
        texture_path = os.path.join('textures', texture_set_info['texture_set'])
        self.read = JsonFileHandler(texture_path)
        # 这里保留一个碰撞体实体，不需要渲染它本身
        self.entity = Entity(position=position, collider='box', scale=1)
        self.face_top = Entity(model='quad', position=(0, 0.5, 0), scale=(1, 1), rotation_x=90, parent=self.entity, texture=self.read.get("top_tex"), double_sided=True)
        self.face_side_left = Entity(model='quad', position=(0, 0, 0.5), scale=(1, 1), rotation_y=0, parent=self.entity, texture=self.read.get("side_tex"), double_sided=True)
        self.face_side_right = Entity(model='quad', position=(0, 0, -0.5), scale=(1, 1), rotation_y=180, parent=self.entity, texture=self.read.get("side_tex"), double_sided=True)
        self.face_side_front = Entity(model='quad', position=(0.5, 0, 0), scale=(1, 1), rotation_y=90, parent=self.entity, texture=self.read.get("side_tex"), double_sided=True)
        self.face_side_back = Entity(model='quad', position=(-0.5, 0, 0), scale=(1, 1), rotation_y=270, parent=self.entity, texture=self.read.get("side_tex"), double_sided=True)
        self.face_bottom = Entity(model='quad', position=(0, -0.5, 0), scale=(1, 1), rotation_x=90, parent=self.entity, texture=self.read.get("bottom_tex"), double_sided=True)
        self.entity.block = self

class Particle():
    def __init__(self, position=(0, 0, 0), particleBlockId=1):
        texture_set_info = JsonFileHandler('textures/textureSets.json').get(str(particleBlockId))
        texture_path = os.path.join('textures', texture_set_info['texture_set'])
        self.read = JsonFileHandler(texture_path)
        self.entity = Entity(position=position, model='quad', scale=(0.18, 0.18), texture=choice(self.read.get("particle_texs")), double_sided=True, billboard=True)
        self.velocity = Vec3(uniform(-1, 1), uniform(0.7, 1.5), uniform(-1, 1)) * 1.2
        self.life = 0.0
        self.ttl = PARTICLE_LIFETIME

blockList = []
particleList = []
MINING_FREEZE_TIME = 0.3
PLACING_FREEZE_TIME = 0.3
PARTICLE_LIFETIME = 0.5
last_mine_time = 0.0
last_place_time = 0.0
selected_item = 1

for x in range(-7, 6):
    for z in range(-7, 6):
        block = Block(position=(x, 0, z), blockId=1)
        blockList.append(block)


def get_block_from_hit(entity):
    if hasattr(entity, 'block'):
        return entity
    if entity.parent is not None and hasattr(entity.parent, 'block'):
        return entity.parent
    return None

def get_selected_slot():
    for i in range(1, 10):
        if held_keys[str(i)]:
            return i
    return None


def spawn_particles(position, blockId, count=8):
    for i in range(count):
        offset = Vec3(uniform(-0.2, 0.2), uniform(-0.1, 0.1), uniform(-0.2, 0.2))
        p = Particle(position=position + offset, particleBlockId=blockId)
        particleList.append(p)


def update_particles():
    for particle in particleList[:]:
        particle.life += time.dt
        particle.entity.position += particle.velocity * time.dt
        particle.entity.scale *= 0.96
        if particle.life >= particle.ttl:
            destroy(particle.entity)
            particleList.remove(particle)


def update():
    global last_mine_time, last_place_time, selected_item

    slot = get_selected_slot()
    if slot is not None:
        selected_item = slot

    if held_keys['f'] and held_keys['escape']:
        quit()

    now = time.time()
    origin = camera.world_position
    direction = camera.forward

    if held_keys['left mouse'] and now - last_mine_time >= MINING_FREEZE_TIME:
        hit = raycast(origin, direction, distance=8, traverse_target=scene, ignore=(player,))
        if hit.hit:
            block_entity = get_block_from_hit(hit.entity)
            if block_entity:
                block = block_entity.block
                spawn_particles(block_entity.position, block.blockId, count=8)
                block.entity.disable()
                if block in blockList:
                    blockList.remove(block)
                last_mine_time = now

    if held_keys['right mouse'] and now - last_place_time >= PLACING_FREEZE_TIME:
        hit = raycast(origin, direction, distance=8, traverse_target=scene, ignore=(player,))
        if hit.hit:
            block_entity = get_block_from_hit(hit.entity)
            if block_entity:
                place_pos = block_entity.position + hit.normal
                place_pos = Vec3(round(place_pos.x), round(place_pos.y), round(place_pos.z))
                if not any(b.entity.position == place_pos for b in blockList):
                    Block(position=place_pos, blockId=selected_item)
                    last_place_time = now
    if player.y <= -30:
        player.gravity = 0
        player.y = 5
        player.gravity = 0.83

    update_particles()
app.run()