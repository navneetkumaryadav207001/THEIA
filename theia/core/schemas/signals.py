from pydantic import BaseModel

class CircadianSignal(BaseModel):
    data_points_count:int
    hourly_distribution:list[float]
    circular_mean_hour_utc:float
    inferred_timezone:str
    sleep_window_start_utc:float
    sleep_window_end_utc:float
    confidence:float