from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import os
import time
from random import choice, uniform
from blockTypes import Block, GravityBlock, Particle, create_block

app = Ursina()
Sky()
player = FirstPersonController(y=2, gravity=0.8)

particleList = []
MINING_FREEZE_TIME = 0.3
PLACING_FREEZE_TIME = 0.3
PARTICLE_LIFETIME = 0.5 
last_mine_time = 0.0
last_place_time = 0.0
selected_item = 1

for x in range(-7, 6):
    for z in range(-7, 6):
        from blockTypes import create_block
        create_block(position=(x, 0, z), blockId=1)


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
                block.destroy()
                last_mine_time = now

    if held_keys['right mouse'] and now - last_place_time >= PLACING_FREEZE_TIME:
        hit = raycast(origin, direction, distance=8, traverse_target=scene, ignore=(player,))
        if hit.hit:
            block_entity = get_block_from_hit(hit.entity)
            if block_entity:
                place_pos = block_entity.position + hit.normal
                place_pos = Vec3(round(place_pos.x), round(place_pos.y), round(place_pos.z))
                if not any(b.entity.position == place_pos for b in Block.instances):
                    create_block(position=place_pos, blockId=selected_item)
                    last_place_time = now
    if player.y <= -30:
        player.gravity = 0
        player.y = 5
        player.gravity = 0.83

    for block in [b for b in list(Block.instances) if isinstance(b, GravityBlock)]:
        block.update(time.dt, Block.instances)
    update_particles()

app.run()