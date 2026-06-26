from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from L3dbackfrontUtils import LocalStorage
import time

app = Ursina()
Sky()

cubeObj = []
player = FirstPersonController(y=4, speed=6, gravity=0.8)

destroy_cooldown = 0.2
place_cooldown = 0.2
last_destroy = 0
last_place = 0
selected_block = 1
json_data = LocalStorage("blocks.json")

# 普通方块
def create_normal_cube(pos, tex_path):
    return Entity(
        position=pos,
        model='cube',
        texture=tex_path,
        collider='box'
    )

# 草方块
def create_grass_cube(pos, top_tex, side_tex, bottom_tex):
    root = Entity(position=pos, collider='box')
    h = 0.5
    Entity(parent=root, model='quad', texture=top_tex, position=(0, h, 0), rotation_x=90, scale=(h, h))
    Entity(parent=root, model='quad', texture=bottom_tex, position=(0, -h, 0), rotation_x=-90, scale=(h, h))
    Entity(parent=root, model='quad', texture=side_tex, position=(0, 0, h), scale=(h, h))
    Entity(parent=root, model='quad', texture=side_tex, position=(0, 0, -h), rotation_y=180, scale=(h, h))
    Entity(parent=root, model='quad', texture=side_tex, position=(h, 0, 0), rotation_y=90, scale=(h, h))
    Entity(parent=root, model='quad', texture=side_tex, position=(-h, 0, 0), rotation_y=-90, scale=(h, h))
    return root

# 地面初始化
for x in range(-4, 4):
    for z in range(-4, 4):
        blk = create_normal_cube((x,0,z), json_data.getItem("1")["tex"])
        cubeObj.append(blk)

def update():
    global last_destroy, last_place, selected_block
    if held_keys['escape']:
        application.quit()

    hit_info = raycast(camera.world_position, camera.forward, distance=20, ignore=[player])

    # 左键拆除
    if held_keys['left mouse'] and time.time() - last_destroy > destroy_cooldown:
        if hit_info.hit and hit_info.entity in cubeObj:
            last_destroy = time.time()
            cubeObj.remove(hit_info.entity)
            destroy(hit_info.entity)

    # 右键放置
    if held_keys['right mouse'] and time.time() - last_place > place_cooldown:
        if hit_info.hit and hit_info.entity in cubeObj:
            last_place = time.time()
            pos = hit_info.entity.position + hit_info.normal
            bid = str(selected_block)
            data = json_data.getItem(bid)
            if bid == "3":
                new_blk = create_grass_cube(pos, data["top"], data["side"], data["bottom"])
            else:
                new_blk = create_normal_cube(pos, data["tex"])
            cubeObj.append(new_blk)
    

    # 方块切换
    if held_keys['1']:
        selected_block = 1
    if held_keys['2']:
        selected_block = 2
    if held_keys['3']:
        selected_block = 3

app.run()