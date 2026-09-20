import numpy as np
def calculate_circular_mean(utc_hours: list[float]) -> tuple[float,float]:
    """Returns (mean_hour_utc,R_bar_concentration)"""
    if len(utc_hours) == 0:
        return (0.0,0.0)
    two_pi = 2*np.pi
    hours_array = np.array(utc_hours)
    theta_array = two_pi * hours_array/24
    x_array = np.cos(theta_array)
    y_array = np.sin(theta_array)
    c_bar = np.mean(x_array)
    s_bar = np.mean(y_array)
    theta = np.arctan2(s_bar,c_bar) % two_pi
    circular_mean = theta * 24 / two_pi
    R = np.sqrt(c_bar**2 + s_bar**2)

    return circular_mean, R