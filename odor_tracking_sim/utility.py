import scipy
import math


def rotate_vecs(x,y,angle):
    xrot = x*scipy.cos(angle) - y*scipy.sin(angle)
    yrot = x*scipy.sin(angle) + y*scipy.cos(angle)
    return xrot, yrot


def shift_and_rotate(p, shift, angle):
    p_vec = scipy.array(p)
    shift_vec = scipy.array(shift)
    rot_mat = rotation_matrix(angle)
    if len(p_vec.shape) > 1:
        shift_vec = scipy.reshape(shift_vec,(2,1))
    return scipy.dot(rot_mat, p_vec - shift_vec)


def rotation_matrix(angle):
    A = scipy.array([
        [scipy.cos(angle), -scipy.sin(angle)],
        [scipy.sin(angle),  scipy.cos(angle)]
        ])
    return A


def create_circle_of_sources(number,radius,strength):
    location_list = []
    for i in range(number):
        angle = i*(2.0*scipy.pi)/number
        x = radius*scipy.cos(angle)
        y = radius*scipy.sin(angle)
        location_list.append((x,y))
    strength_list = [strength for x in location_list]
    return location_list, strength_list


def create_grid_of_sources(x_num, y_num, x_range, y_range,  strength):
    x_vals = scipy.linspace(x_range[0], x_range[1], x_num)
    y_vals = scipy.linspace(y_range[0], y_range[1], y_num)
    location_list = [(x,y) for x in x_vals for y in y_vals]
    strength_list = [strength for x in location_list]
    return location_list, strength_list


def distance(p,q):
    return scipy.sqrt((p[0]-q[0])**2 + (p[1]-q[1])**2)


def unit_vector(x,y): 
    v_mag = scipy.sqrt(x**2 + y**2)
    if type(v_mag) == scipy.ndarray:
        mask = v_mag > 0
        x_unit = scipy.zeros(x.shape)
        y_unit = scipy.zeros(y.shape)
        x_unit[mask] = x/v_mag
        y_unit[mask] = y/v_mag
    else:
        if (v_mag > 0):
            x_unit = x/v_mag
            y_unit = y/v_mag
        else:
            x_unit = 0.0
            y_unit = 0.0
    return x_unit, y_unit


def logistic(x,x0,k):
    return 1.0/(1.0 + scipy.exp(-k*(x-x0)))


# Testing/development
# --------------------------------------------------------------------
if __name__ == '__main__':

    import matplotlib.pyplot as plt

    x = scipy.randn(10)
    y = scipy.randn(10)

    loc = (1.0,1.0)

    vals = distance((x,y), loc)
    print(vals)

    location_list, strength_list = create_grid_of_sources(4,3,(-1000,1000),(-1000,1000), 1.0)
    print(location_list)
    print(strength_list)







