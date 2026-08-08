import secrets

from app.application.ports import DiceRoller


class SecureDiceRoller(DiceRoller):
    def roll_d6(self) -> int:
        return secrets.randbelow(6) + 1
