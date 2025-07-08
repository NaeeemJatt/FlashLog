
import abc
import attr

class Config(abc.ABC):
    @classmethod
    def from_dict(cls, config_dict):
        
        if config_dict is None:
            config_dict = {}

        config = cls()
        for field in config.__dict__:

            if field in config_dict:
                setattr(config, field, config_dict[field])
        return config

    def as_dict(self):
        return attr.asdict(self)
