from dataclasses import dataclass

@dataclass
class Box:
    x: int
    y: int
    w: int
    h: int
    label: str
    conf: float

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)

    def resized(self, size: int) -> "Box":
        cx, cy = self.center
        return Box(cx - size // 2, cy - size // 2, size, size, self.label, self.conf)
