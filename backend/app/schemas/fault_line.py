from app.schemas.static_layer import StaticLayer


class FaultLine(StaticLayer):
    max_magnitude_estimate: float | None = None
