from typing import Generator

import attr
from pynput import keyboard

from rogue.generic.ecs import EntityComponentDatabase
from rogue.components import (
    ComponentUnion,
    VelocityComponent,
)
from rogue.systems.common.actions import (
    ActionUnion,
    AddComponentAction,
)
from rogue.systems.common.traits import YieldChangesSystemTrait
from rogue.exceptions import QuitGameException, IgnoreTimeStepException
from rogue.systems.control_systems.functions import get_hero_entity, maybe_equip_next_weapon, maybe_drink_potion


@attr.s(frozen=True, kw_only=True, hash=False, cmp=False)
class PynputHeroControlSystem(YieldChangesSystemTrait):
    upwards: int = attr.ib()
    downwards: int = attr.ib()
    timeout: float = attr.ib()

    @classmethod
    def create(cls, upwards: int = 1, downwards: int = -1, timeout: float = 0.25) -> "PynputHeroControlSystem":
        return cls(upwards=upwards, downwards=downwards, timeout=timeout)

    def __hash__(self) -> int:
        return 0

    def __call__(self, *, ecdb: EntityComponentDatabase[ComponentUnion]) -> Generator[ActionUnion, None, None]:

        hero_entity = get_hero_entity(ecdb=ecdb)

        with keyboard.Events() as events:
            event = events.get(timeout=self.timeout)
            print(event)
            if isinstance(event, keyboard.Events.Press):

                hero_velocity_y, hero_velocity_x = 0, 0

                if event.key == keyboard.Key.esc:
                    raise QuitGameException

                if event.key == keyboard.Key.left:
                    hero_velocity_x = -1
                elif event.key == keyboard.Key.right:
                    hero_velocity_x = 1
                elif event.key == keyboard.Key.up:
                    hero_velocity_y = self.upwards
                elif event.key == keyboard.Key.down:
                    hero_velocity_y = self.downwards
                elif event.key == keyboard.KeyCode.from_char("e"):
                    yield from maybe_equip_next_weapon(ecdb=ecdb, entity=hero_entity)
                    return
                elif event.key == keyboard.KeyCode.from_char("p"):
                    yield from maybe_drink_potion(ecdb=ecdb, entity=hero_entity)
                    return
                else:
                    raise IgnoreTimeStepException

                if hero_velocity_y != 0 or hero_velocity_x != 0:
                    velocity_component = VelocityComponent.create_from_attributes(
                        y_axis=hero_velocity_y, x_axis=hero_velocity_x
                    )
                    yield AddComponentAction(entity=hero_entity, component=velocity_component)
                    return
            else:
                raise IgnoreTimeStepException
