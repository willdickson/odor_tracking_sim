import scipy


class ConstantWindField(object):
    """
    Super simple constant wind model specified by wind angle and speed.
    """

    DefaultParam = { 'angle': 0.0, 'speed': 1.0 }

    def __init__(self,param={}):

        self.param = dict(self.DefaultParam)
        self.param.update(param)

        self.angle = param['angle']
        self.speed = param['speed']

    def value(self,t,x,y):
        vx = self.speed*scipy.cos(self.angle)
        vy = self.speed*scipy.sin(self.angle)
        if type(x) == scipy.ndarray:
            if x.shape != y.shape:
                raise(ValueError,'x.shape must equal y.shape')
            vx_array = scipy.full(x.shape,vx)
            vy_array = scipy.full(y.shape,vy)
            return vx_array, vy_array
        else:
            return vx, vy


# Below here just for testing/development
# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':

    param = { 'angle': 0.0, 'speed': 1.0 }

    wind_field = ConstantWindField(param=param)
    num_pts = 100
    x = scipy.linspace(-1.0,1.0,num_pts)
    y = scipy.linspace(-1.0,1.0,num_pts)
    wind_values = wind_field.value(0.1,x,y)
    print(type(wind_field)==ConstantWindField)



