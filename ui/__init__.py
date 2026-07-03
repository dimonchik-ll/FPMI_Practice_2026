from ui.economy import Economy

__all__ = ["Economy", "UiSystem"]


def __getattr__(name: str):
    if name == "UiSystem":
        from ui.api import UiSystem

        return UiSystem
    raise AttributeError(name)
