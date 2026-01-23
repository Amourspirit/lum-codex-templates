from dataclasses import dataclass


@dataclass
class ApiEnv:
    dev: str
    prod: str
    test: str
