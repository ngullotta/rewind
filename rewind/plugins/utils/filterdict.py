from typing import Any


class FilteredDict(dict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.filter = kwargs.pop("filter")
        self.__cull()

    def __cull(self) -> None:
        if self.filter is None:
            return

        unwanted = [k for k in self if k not in self.filter]
        for k in unwanted:
            del self[k]

    def __setitem__(self, k, v) -> Any:
        if k in self.filter.keys():
            return super().__setitem__(k, v)
