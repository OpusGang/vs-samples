from dataclasses import dataclass, field, replace, fields
from typing import Callable, Any, Optional, Type
import inspect

from .enums import Compatibility, EOTF, Gamut, IQ, SubBlack, SuperWhite, HalfLine
from .types import ColorbarsSettings

@dataclass(slots=True)
class Signature:
    settings: ColorbarsSettings
    defaults: dict[str, Any]
    changed: dict[str, Any] = field(init=False, default_factory=dict)

    @classmethod
    def generate(
        cls,
        fn: Callable[..., Any],
        settings: ColorbarsSettings,
    ) -> "Signature":

        sig = inspect.signature(fn)

        settings_keys = set(vars(settings))

        defaults: dict[str, Any] = {
            name: param.default
            for name, param in sig.parameters.items()
            if (param.default is not inspect._empty) and (name in settings_keys)
        }

        return cls(settings, defaults)

    def __post_init__(self):
        settings = vars(self.settings)

        self.changed = {
            k: settings[k]
            for k, default in self.defaults.items()
            if (k in settings) and (settings[k] != default)
        }

class Helper:
    @staticmethod
    def settings_from_signature(fn: Callable[..., Any], cls: Type[ColorbarsSettings]) -> ColorbarsSettings:
        sig = inspect.signature(fn)

        names = {f.name for f in fields(cls)}

        base = {
            n: p.default
            for n, p in sig.parameters.items()
            if (n in names) and (p.default is not inspect._empty)
        }

        return cls(**base)


    @staticmethod
    def resolve_settings(
        fn: Callable[..., Any],
        preset: Optional[ColorbarsSettings] = None,
        **user_args
    ) -> ColorbarsSettings:

        base = Helper.settings_from_signature(fn, ColorbarsSettings)

        merged = base if preset is None else replace(base, **vars(preset))

        base_keys = set(vars(base))

        final_overrides = {k: v for k, v in user_args.items() if k in base_keys}
        return replace(merged, **final_overrides)


class Generator:
    @staticmethod
    def generate_settings(
        preset: ColorbarsSettings,
        compatibility: Compatibility,
        subblack: SubBlack,
        superwhite: SuperWhite,
        iq: IQ,
        halfline: HalfLine
    ) -> ColorbarsSettings:

        return replace(
            preset,
            compatibility=compatibility,
            subblack=subblack,
            superwhite=superwhite,
            iq=iq,
            halfline=halfline
        )
