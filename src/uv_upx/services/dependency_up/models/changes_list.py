from pydantic import BaseModel

from uv_upx.services.dependency_up.models.dependency_parsed import DependencyParsed


class ChangesItem(BaseModel):
    from_item: DependencyParsed
    to_item: DependencyParsed

    def __str__(self) -> str:
        return (
            f"{self.from_item.get_name_with_extras()}: "
            f"{self.from_item.get_partial_spec()}"
            f" -> "
            f"{self.to_item.get_partial_spec()}"
        )


type ChangesList = list[ChangesItem]
