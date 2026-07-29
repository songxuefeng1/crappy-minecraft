from ursina import *
from l3dBackfront import JsonFileHandler
from random import uniform, choice
import os


def _to_vec3(v):
    """Normalize different scale/position representations to a Vec3."""
    if isinstance(v, Vec3):
        return v
    if isinstance(v, (int, float)):
        return Vec3(v, v, v)
    if isinstance(v, (tuple, list)):
        return Vec3(*v)
    return Vec3(v)

MINING_FREEZE_TIME = 0.3
PLACING_FREEZE_TIME = 0.3
PARTICLE_LIFETIME = 0.5

class Block():
    instances = []
    UNKNOWN_TEXTURE_PATH = os.path.join('textures', 'unknowBlock/textureSet.json')
    FACE_OFFSETS = {
        'top': (Vec3(0, 0.5, 0), Vec3(90, 0, 0), 'top_tex'),
        'bottom': (Vec3(0, -0.5, 0), Vec3(90, 0, 0), 'bottom_tex'),
        'left': (Vec3(0, 0, 0.5), Vec3(0, 0, 0), 'side_tex'),
        'right': (Vec3(0, 0, -0.5), Vec3(0, 180, 0), 'side_tex'),
        'front': (Vec3(0.5, 0, 0), Vec3(0, 90, 0), 'side_tex'),
        'back': (Vec3(-0.5, 0, 0), Vec3(0, 270, 0), 'side_tex'),
    }

    def __init__(self, position=(0, 0, 0), blockId=1):
        self.blockId = blockId
        texture_set_info = JsonFileHandler('textures/textureSets.json').get(str(blockId), {})
        texture_path = texture_set_info.get('texture_set')
        if not texture_path:
            texture_path = Block.UNKNOWN_TEXTURE_PATH
        else:
            texture_path = os.path.join('textures', texture_path)
            if not os.path.exists(texture_path):
                texture_path = Block.UNKNOWN_TEXTURE_PATH

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
        self.entity.block_instance = self
        Block.instances.append(self)

    def update(self, dt=0, block_list=None):
        pass

    def destroy(self):
        if self in Block.instances:
            Block.instances.remove(self)
        # remove self from instances first so schedule_above_fall sees the world without this block
        schedule_above_fall(self.entity.position)
        destroy(self.entity)

    def get_bounds(self):
        pos = Vec3(self.entity.world_position)
        scale = _to_vec3(self.entity.scale)
        half = scale / 2
        return pos - half, pos + half

    @classmethod
    def get_block_at(cls, position):
        pos = Vec3(round(position.x), round(position.y), round(position.z))
        for block in cls.instances:
            ent_pos = block.entity.position
            if Vec3(round(ent_pos.x), round(ent_pos.y), round(ent_pos.z)) == pos:
                return block
        return None


def get_entity(obj):
    """Return an Entity for a given input.

    Accepts:
    - Entity -> returns it
    - Block (or any object with `.entity`) -> returns `.entity` if it's an Entity
    - Entity-like objects -> returns None if not resolvable
    """
    if isinstance(obj, Entity):
        return obj
    if isinstance(obj, Block):
        return obj.entity
    ent = getattr(obj, 'entity', None)
    if isinstance(ent, Entity):
        return ent
    return None


def schedule_above_fall(position):
    target_x = round(position.x)
    target_z = round(position.z)
    target_y = round(position.y)
    for block in list(Block.instances):
        if not isinstance(block, GravityBlock):
            continue
        if round(block.entity.x) != target_x or round(block.entity.z) != target_z:
            continue
        if round(block.entity.y) <= target_y:
            continue
        if not block.is_supported():
            if block not in GravityBlock.falling_blocks:
                GravityBlock.falling_blocks.append(block)

class GravityBlock(Block):
    falling_blocks = []

    def __init__(self, position=(0, 0, 0), blockId=1):
        super().__init__(position, blockId)
        if not self.is_supported():
            GravityBlock.falling_blocks.append(self)

    def isOverLap(self, target):
        """Accept either an `Entity` or a `Block` (or an object with `.entity`) and test AABB overlap."""
        target_entity = get_entity(target)
        if target_entity is None:
            return False

        a_pos = Vec3(self.entity.world_position)
        b_pos = Vec3(target_entity.world_position)

        a_scale = _to_vec3(self.entity.scale)
        b_scale = _to_vec3(target_entity.scale)

        a_min = a_pos - a_scale / 2
        a_max = a_pos + a_scale / 2
        b_min = b_pos - b_scale / 2
        b_max = b_pos + b_scale / 2

        overlap_x = (a_min.x < b_max.x) and (a_max.x > b_min.x)
        overlap_y = (a_min.y < b_max.y) and (a_max.y > b_min.y)
        overlap_z = (a_min.z < b_max.z) and (a_max.z > b_min.z)

        return overlap_x and overlap_y and overlap_z

    def update(self, dt=0, block_list=None):
        if block_list is None:
            block_list = Block.instances

        if self.is_supported(block_list):
            self.entity.y = round(self.entity.y)
            if self in GravityBlock.falling_blocks:
                GravityBlock.falling_blocks.remove(self)
            return

        if self not in GravityBlock.falling_blocks:
            GravityBlock.falling_blocks.append(self)

        self.entity.y -= 8 * dt
        if self.entity.y < -10:
            self.destroy()

    def destroy(self):
        if self in GravityBlock.falling_blocks:
            GravityBlock.falling_blocks.remove(self)
        super().destroy()

    def schedule_above_fall(self):
        schedule_above_fall(self.entity.position)

    def is_supported(self, block_list=None):
        if block_list is None:
            block_list = Block.instances

        target_x = round(self.entity.x)
        target_z = round(self.entity.z)
        target_y = round(self.entity.y) - 1

        for block in block_list:
            if block is self:
                continue
            if round(block.entity.x) != target_x or round(block.entity.z) != target_z:
                continue
            if round(block.entity.y) != target_y:
                continue

            self.entity.y = round(block.entity.y) + 1
            return True

        return False


def create_block(position=(0, 0, 0), blockId=1):
    texture_set_info = JsonFileHandler('textures/textureSets.json').get(str(blockId), {})
    texture_path = texture_set_info.get('texture_set')
    if texture_path:
        full_path = os.path.join('textures', texture_path)
        if os.path.exists(full_path):
            child_info = JsonFileHandler(full_path).read()
            if child_info.get('blockModelTemplate') == 'gravity':
                return GravityBlock(position=position, blockId=blockId)
            if child_info.get('blockModelTemplate') == 'GlassTex':
                return GlassBlock(position=position, blockId=blockId)
    return Block(position=position, blockId=blockId)


class GlassBlock(Block):
    def __init__(self, position=(0, 0, 0), blockId=1):
        self.blockId = blockId
        texture_set_info = JsonFileHandler('textures/textureSets.json').get(str(blockId), {})
        texture_path = texture_set_info.get('texture_set')
        if not texture_path:
            texture_path = Block.UNKNOWN_TEXTURE_PATH
        else:
            texture_path = os.path.join('textures', texture_path)
            if not os.path.exists(texture_path):
                texture_path = Block.UNKNOWN_TEXTURE_PATH

        self.read = JsonFileHandler(texture_path)
        self.entity = Entity(position=position, collider='box', scale=1)
        self.entity.block = self
        self.entity.block_instance = self
        self.faces = {}
        Block.instances.append(self)
        self.refresh_faces()
        self.refresh_neighbor_faces()

    def create_face(self, offset, rotation, texture):
        return Entity(
            model='quad',
            position=offset,
            rotation=rotation,
            scale=(1, 1),
            parent=self.entity,
            texture=texture,
            double_sided=True,
            transparent=True,
            alpha_mode='blend'
        )

    def should_show_face(self, offset):
        neighbor = Block.get_block_at(self.entity.position + offset)
        if neighbor is None:
            return True
        return not isinstance(neighbor, GlassBlock)

    def refresh_faces(self):
        for face in self.faces.values():
            if face:
                destroy(face)
        self.faces = {}

        for name, (offset, rotation, tex_key) in self.FACE_OFFSETS.items():
            if self.should_show_face(offset):
                texture = self.read.get(tex_key)
                self.faces[name] = self.create_face(offset, rotation, texture)
            else:
                self.faces[name] = None

    def refresh_neighbor_faces(self):
        for offset, _, _ in self.FACE_OFFSETS.values():
            neighbor = Block.get_block_at(self.entity.position + offset)
            if isinstance(neighbor, GlassBlock):
                neighbor.refresh_faces()

    def destroy(self):
        positions = [self.entity.position + offset for offset, _, _ in self.FACE_OFFSETS.values()]
        super().destroy()
        for pos in positions:
            neighbor = Block.get_block_at(pos)
            if isinstance(neighbor, GlassBlock):
                neighbor.refresh_faces()


class Particle():
    def __init__(self, position=(0, 0, 0), particleBlockId=1):
        texture_set_info = JsonFileHandler('textures/textureSets.json').get(str(particleBlockId), {})
        texture_path = texture_set_info.get('texture_set')
        if texture_path:
            texture_path = os.path.join('textures', texture_path)
            if not os.path.exists(texture_path):
                texture_path = Block.UNKNOWN_TEXTURE_PATH
        else:
            texture_path = Block.UNKNOWN_TEXTURE_PATH

        self.read = JsonFileHandler(texture_path)
        self.entity = Entity(position=position, model='quad', scale=(0.18, 0.18), texture=choice(self.read.get("particle_texs")), double_sided=True, billboard=True)
        self.velocity = Vec3(uniform(-1, 1), uniform(0.7, 1.5), uniform(-1, 1)) * 1.2
        self.life = 0.0
        self.ttl = PARTICLE_LIFETIME
