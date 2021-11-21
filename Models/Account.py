#################
# Account Class #
#################

from dataclasses import dataclass, field


@dataclass
class Account:
    
    
    
    def __post_init__(self) -> None:
        self.trades = []