def linear_interpolate(xy_coords, x):
    if x < xy_coords[0][0] or x > xy_coords[-1][0]:
        raise RuntimeError("the x value is out of the interpolation range")
    for i in range(len(xy_coords) - 1):
        x0, y0 = xy_coords[i]
        x1, y1 = xy_coords[i + 1]        
        if x0 <= x <= x1:
            y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
            return y
    raise RuntimeError("interpolation failed due to unexpected input")

