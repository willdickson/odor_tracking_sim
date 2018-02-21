from __future__ import print_function
import scipy

from utility import unit_vector
from utility import shift_and_rotate


class VerySimpleFly(object):
    """
    Old non-vectorized model for flies.

    """

    DefaultParam = {
            'initial_heading'     : scipy.radians(0.0),
            'heading_error_std'   : scipy.radians(10.0),
            'start_position'      : (0.0, 0.0),
            'flight_speed'        : 0.2,
            'release_time'        : 0.0,
            'cast_interval'       : [10.0, 500.0],
            'wind_slippage'       : 0.0,
            'odor_thresholds'     : {
                'lower': 0.001,
                'upper': 0.0015
                },
            'odor_probabilities'  : {
                'lower': 0.9, 
                'upper': 0.9
                }
            }

    Mode_FixHeading = 0
    Mode_FlyUpWind = 1
    Mode_CastForOdor = 2
    Mode_Trapped = 3

    def __init__(self,param={}):

        self.param = dict(self.DefaultParam)
        self.param.update(param)

        self.position = self.param['start_position'] 
        self.mode = self.Mode_FixHeading 

        self.heading_error = None
        self.t_last_cast = None
        self.dt_next_cast = None
        self.cast_sign = None
        self.trap_num = None
        self.trap_loc = None

    @property
    def odor_threshold(self):
        if self.mode == self.Mode_FlyUpWind:
            return self.param['odor_thresholds']['lower']
        else:
            return self.param['odor_thresholds']['upper']


    @property
    def odor_probability(self):
        if self.mode == self.Mode_FlyUpWind:
            return self.param['odor_probabilities']['lower']
        else:
            return self.param['odor_probabilities']['upper']


    @property
    def x(self):
        return self.position[0]

    @property
    def y(self):
        return self.position[1]

    def add_heading_error(self,v):
        return shift_and_rotate(v,(0,0),self.heading_error)

    def update(self, t, dt, wind_field, odor_field):

        if t < self.param['release_time']:
            # If not yet releases do nothing
            return
        if self.mode == self.Mode_Trapped:
            return

        x, y = self.position
        speed = self.param['flight_speed']
        x_wind, y_wind =  wind_field.value(t,x,y)
        x_wind_unit, y_wind_unit = unit_vector(x_wind,y_wind)

        # Update position based on mode
        x_step, y_step = 0.0, 0.0
        if self.mode == self.Mode_FixHeading:
            angle = self.param['initial_heading']
            x_step = dt*speed*scipy.cos(angle)
            y_step = dt*speed*scipy.sin(angle)

        elif self.mode == self.Mode_FlyUpWind:
            x_head_unit, y_head_unit = self.add_heading_error((x_wind_unit,y_wind_unit)) 
            x_step = -dt*speed*x_head_unit
            y_step = -dt*speed*y_head_unit

        elif self.mode == self.Mode_CastForOdor:
            if self.t_last_cast is None:
                self.t_last_cast = t
                self.dt_next_cast = 0.0
                self.cast_sign = scipy.random.choice([-1,1])
            if self.t_last_cast + self.dt_next_cast < t:
                self.cast_sign *= -1
                self.t_last_cast = t
                self.dt_next_cast = scipy.random.uniform(*self.param['cast_interval'])

            x_head_unit, y_head_unit = self.add_heading_error((x_wind_unit,y_wind_unit)) 
            x_step =  self.cast_sign*dt*speed*x_head_unit 
            y_step = -self.cast_sign*dt*speed*y_head_unit

        else:
            raise RuntimeError, 'unexpected mode {0}'.format(self.mode)

        x_step += dt*self.param['wind_slippage']*x_wind
        y_step += dt*self.param['wind_slippage']*y_wind
        self.position = self.position[0] + x_step, self.position[1] + y_step 

        # Check if in trap
        in_trap, trap_num, trap_loc = odor_field.check_if_in_trap(self.position)
        if in_trap:
            self.mode = self.Mode_Trapped 
            self.trap_num = trap_num
            self.trap_loc = trap_loc
        else:
            # Check odor for mode change
            odor_value = odor_field.value(t,x,y)

            mode_change = False
            if odor_value > self.odor_threshold:
                if self.mode != self.Mode_FlyUpWind:
                    if scipy.rand() < self.odor_probability: 
                        self.mode = self.Mode_FlyUpWind
                        mode_change = True
            else:
                if self.mode != self.Mode_FixHeading:
                    if self.mode != self.Mode_CastForOdor:
                        if scipy.rand() < self.odor_probability:
                            self.mode = self.Mode_CastForOdor 
                            mode_change = True
            if mode_change:
                self.heading_error = self.param['heading_error_std']*scipy.randn(1)[0]



# Below here just for Testing/development
# -------------------------------------------------------------------------------------------------
if __name__ == '__main__':

    pass

    #import time
    #import wind_models
    #import odor_models
    #import matplotlib.pyplot as plt
    #from utility import create_circle_of_sources


    ## Create constant wind field
    #wind_param = {
    #        'speed': 0.5,
    #        'angle': 25.0*scipy.pi/180.0,
    #        }
    #wind_field = wind_models.ConstantWindField(param=wind_param)

    ## Create scalar odor concentration field
    ## Source location and strength
    #number_sources = 6
    #radius_sources = 1000.0 
    #strength_sources = 10.0

    #location_list, strength_list = create_circle_of_sources(
    #        number_sources,
    #        radius_sources,
    #        strength_sources
    #        )
    #odor_param = {
    #        'wind_field'       : wind_field, 
    #        'diffusion_coeff'  :  0.25,
    #        'source_locations' : location_list, 
    #        'source_strengths' : strength_list,
    #        'epsilon'          : 0.01,
    #        'trap_radius'      : 1.0
    #        }
    #odor_field = odor_models.FakeDiffusionOdorField(odor_param)

    #num_fly = 200 

    #fly_param = {
    #        'heading_error_std'   : scipy.radians(10.0),
    #        'start_position'      : (0.0, 0.0),
    #        'flight_speed'        : 0.7,
    #        'release_time'        : 0.0,
    #        'cast_interval'       : [60.0, 1000.0],
    #        'wind_slippage'       : 0.5,
    #        'odor_thresholds'     : {
    #            'lower': 0.001,
    #            'upper': 0.0015
    #            },
    #        'odor_probabilities'  : {
    #            'lower': 0.9, 
    #            'upper': 0.001,
    #            },
    #        }
    #fly_list = []

    #if True:
    #    heading_array = scipy.linspace(0.0,2.0*scipy.pi,num_fly)
    #    for heading in heading_array:
    #        fly_param['initial_heading'] = heading 
    #        fly = VerySimpleFly(param=fly_param)
    #        fly_list.append(fly)
    #else:
    #    for i in range(num_fly):
    #        fly_param['initial_heading'] = scipy.random.uniform(0.0,2.0*scip.pi) 
    #        fly_param['release_time'] = scipy.random.exponential(1000)
    #        fly = VerySimpleFly(param=fly_param)
    #        fly_list.append(fly)

    #fignum = 1
    #plot_scale = 1.5
    #plot_size = plot_scale*radius_sources
    #plot_param = { 
    #        'xlim' : (-plot_size, plot_size),
    #        'ylim' : (-plot_size, plot_size),
    #        'xnum' : 500,
    #        'ynum' : 500,
    #        'cmap' : 'binary',
    #        #'threshold': 0.001,
    #        'fignums' : (1,2),
    #        }
    #odor_field.plot(plot_param=plot_param)
    ##plt.show()

    #plt.ion()
    #fig = plt.figure(fignum)
    #ax = plt.subplot(111)

    #plt.figure(fignum)
    #fly_xvals = [fly.x for fly in fly_list]
    #fly_yvals = [fly.y for fly in fly_list]
    #fly_dots, = plt.plot(fly_xvals, fly_yvals,'.r')

    #fig.canvas.flush_events()
    #plt.pause(0.0001)

    #t = 0.0
    #dt = 1.0 
    #t_stop = 100000.0

    #dt_plot = 10.0
    #t_plot_last = 0.0 

    #while t<t_stop:

    #    print('{0:1.2f}'.format(t))

    #    t0 = time.time()
    #    for fly in fly_list:
    #        fly.update(t, dt, wind_field, odor_field)
    #    t1 = time.time()

    #    if t_plot_last + dt_plot < t:

    #        fly_xvals = [fly.x for fly in fly_list]
    #        fly_yvals = [fly.y for fly in fly_list]
    #        plt.figure(fignum)
    #        fly_dots.set_xdata([fly_xvals])
    #        fly_dots.set_ydata([fly_yvals])

    #        trapped_fly_list = [fly for fly in fly_list if fly.trap_num is not None]
    #        num_trapped = len(trapped_fly_list)

    #        num_in_loc_list = []
    #        for i, loc in enumerate(odor_field.param['source_locations']):
    #            num_in_loc = len([fly for fly in trapped_fly_list if fly.trap_loc == loc])
    #            num_in_loc_list.append(num_in_loc)

    #        plt.title('#trapped {0}/{1}, {2}'.format(num_trapped,len(fly_list),num_in_loc_list))

    #        fig.canvas.flush_events()
    #        t_plot_last = t

    #    t += dt

    #ans = raw_input('done')

                


