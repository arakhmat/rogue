from collections import deque
from typing import (
    cast,
    Optional,
    Tuple,
    List,
    Type,
    Deque,
)

import attr
import pygcurse

from rogue.generic.ecs import (
    EntityComponentDatabase,
    get_component,
    query_entities,
    Entity,
)
from rogue.components import (
    ComponentUnion,
    PositionComponent,
    TypeComponent,
    SizeComponent,
    InventoryComponent,
    MoneyComponent,
)
from rogue.systems.common.traits import NoReturnSystemTrait


def _type_to_appearance(item_type: str) -> Tuple[str, str]:
    item_type_to_appearance = {
        "hero": ("#", "purple"),
        "sword": ("(", "green"),
        "hobgoblin": ("H", "red"),
        "potion": ("!", "blue"),
        "gold": ("*", "gold"),
        "door": ("+", "grey"),
    }
    symbol, color = item_type_to_appearance[item_type]
    return symbol, color


def _render_room(
    *, window: pygcurse.PygcurseWindow, position_component: PositionComponent, size_component: SizeComponent
) -> None:
    height, width = size_component.height, size_component.width

    # Left Wall
    start_pos = position_component.x_axis, position_component.y_axis + 1
    end_pos = position_component.x_axis, position_component.y_axis + height - 1
    window.drawline(char="|", start_pos=start_pos, end_pos=end_pos, fgcolor="grey")

    # Right Wall
    start_pos = position_component.x_axis + width, position_component.y_axis + 1
    end_pos = position_component.x_axis + width, position_component.y_axis + height - 1
    window.drawline(char="|", start_pos=start_pos, end_pos=end_pos, fgcolor="grey")

    # Top Wall
    start_pos = position_component.x_axis, position_component.y_axis
    end_pos = position_component.x_axis + width, position_component.y_axis
    window.drawline(char="_", start_pos=start_pos, end_pos=end_pos, fgcolor="grey")

    # Bottom Wall
    start_pos = position_component.x_axis, position_component.y_axis + height
    end_pos = position_component.x_axis + width, position_component.y_axis + height
    window.drawline(char="_", start_pos=start_pos, end_pos=end_pos, fgcolor="grey")

    # Inside of the Room
    y_axis = position_component.y_axis + 1
    x_axis = position_component.x_axis + 1
    window.fill(char=".", region=(x_axis, y_axis, width - 1, height - 1), fgcolor="grey")


def _render_hero_info(
    *, window: pygcurse.PygcurseWindow, ecdb: EntityComponentDatabase[ComponentUnion], entity: Entity
) -> None:
    x_offset = window.width - 30
    money_component = cast(MoneyComponent, get_component(ecdb=ecdb, entity=entity, component_type=MoneyComponent))
    inventory_component = cast(
        InventoryComponent, get_component(ecdb=ecdb, entity=entity, component_type=InventoryComponent)
    )

    window.fill(char=" ", region=(x_offset, 0, window.width, 2 + len(inventory_component.entities)))

    line = 0

    window.write(text=f"Gold: {money_component.amount}", x=x_offset, y=line, fgcolor="grey")
    line += 1

    window.write(text="Inventory:", x=x_offset, y=line, fgcolor="grey")
    line += 1

    for item in inventory_component.entities:
        type_component = cast(TypeComponent, get_component(ecdb=ecdb, entity=item, component_type=TypeComponent))
        window.write(text=f"    {type_component.entity_type}", x=x_offset, y=line, fgcolor="grey")
        line += 1

    window.write(text="Equipment:", x=x_offset, y=line, fgcolor="grey")


@attr.s(frozen=True, kw_only=True)
class PygcurseRenderSystem(NoReturnSystemTrait):
    window: pygcurse.PygcurseWindow = attr.ib()

    @classmethod
    def create_from_height_and_width(cls, *, height: int, width: int) -> "PygcurseRenderSystem":
        window = pygcurse.PygcurseWindow(width=width, height=height)
        return PygcurseRenderSystem(window=window)

    def __call__(self, *, ecdb: EntityComponentDatabase[ComponentUnion]) -> None:

        dynamic_entities: Deque[Tuple[Entity, PositionComponent, TypeComponent]] = deque(maxlen=None)

        component_types: List[Type[ComponentUnion]] = [PositionComponent, SizeComponent, TypeComponent]
        for entity, components in query_entities(ecdb=ecdb, component_types=component_types):
            position_component = cast(Optional[PositionComponent], components[PositionComponent])
            size_component = cast(Optional[SizeComponent], components[SizeComponent])
            type_component = cast(TypeComponent, components[TypeComponent])

            if position_component is None:
                continue

            # Visualize rooms
            if size_component is not None:
                _render_room(window=self.window, position_component=position_component, size_component=size_component)

            # Defer dynamic entities to make sure all static ones already rendered
            if size_component is None:
                dynamic_entities.append((entity, position_component, type_component))

        # Visualize dynamic entities
        while len(dynamic_entities) > 0:
            entity, position_component, type_component = dynamic_entities.popleft()
            entity_type = type_component.entity_type
            symbol, color = _type_to_appearance(entity_type)
            self.window.putchar(
                symbol, x=position_component.x_axis, y=position_component.y_axis, fgcolor=color,
            )

            if entity_type == "hero":
                _render_hero_info(window=self.window, ecdb=ecdb, entity=entity)