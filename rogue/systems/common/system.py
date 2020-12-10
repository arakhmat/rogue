from typing import Union

from rogue.generic.ecs import (
    EntityComponentDatabase,
    add_component,
    remove_component,
)
from rogue.components import ComponentUnion
from rogue.systems.common.actions import (
    AddComponentAction,
    RemoveComponentAction,
)

from rogue.systems.collision_detection_system import CollisionDetectionSystem
from rogue.systems.enemy_ai_system import EnemyAISystem
from rogue.systems.movement_system import MovementSystem
from rogue.systems.pygame_hero_control_system import PygameHeroControlSystem
from rogue.systems.pygcurse_render_system import PygcurseRenderSystem
from .traits import NoReturnSystemTrait, YieldChangesSystemTrait

SystemUnion = Union[
    PygcurseRenderSystem, MovementSystem, EnemyAISystem, PygameHeroControlSystem, CollisionDetectionSystem
]


def process_system(
    *, system: SystemUnion, ecdb: EntityComponentDatabase[ComponentUnion]
) -> EntityComponentDatabase[ComponentUnion]:
    if isinstance(system, NoReturnSystemTrait):
        system(ecdb=ecdb)
    elif isinstance(system, YieldChangesSystemTrait):
        for entity, action in system(ecdb=ecdb):
            if isinstance(action, AddComponentAction):
                ecdb = add_component(ecdb=ecdb, entity=entity, component=action.component)
            elif isinstance(action, RemoveComponentAction):
                ecdb = remove_component(ecdb=ecdb, entity=entity, component_type=action.component_type)
    else:
        raise ValueError(f"System of type {type(system)} does not support any of the system traits!")
    return ecdb