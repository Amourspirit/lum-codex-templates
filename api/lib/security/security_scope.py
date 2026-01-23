from dataclasses import dataclass, field


@dataclass
class SecurityScope:
    """
    Represents a security scope for route protection.
    Attributes:
        name (str): The name of the scope.
        read_scopes (set[str]): A set of read scopes associated with the scope.
        write_scopes (set[str]): A set of write scopes associated with the scope.
    """

    name: str
    read_scopes: set[str] = field(default_factory=set)
    write_scopes: set[str] = field(default_factory=set)
