from __future__ import print_function
import scipy

from utility import unit_vector
from utility import rotate_vecs
from utility import distance

class BasicSwarmOfFlies(object):

    DefaultSize = 500
    DefaultParam = {
            'initial_heading'     : scipy.radians(scipy.random.uniform(0.0,360.0,(DefaultSize,))),
            'x_start_position'    : scipy.zeros((DefaultSize,)),
            'y_start_position'    : scipy.zeros((DefaultSize,)),
            'heading_error_std'   : scipy.radians(10.0),
            'flight_speed'        : scipy.full((DefaultSize,), 0.7),
            'release_time'        : scipy.full((DefaultSize,), 0.0),
            'cast_interval'       : [60.0, 1000.0],
            'wind_slippage'       : 0.0,
            'odor_thresholds'     : {
                'lower': 0.002,
                'upper': 0.004
                },
            'odor_probabilities'  : {
                'lower': 0.9,    # detection probability/sec of exposure
                'upper': 0.002,  # detection probability/sec of exposure
                } 
            } 

    Mode_FixHeading = 0
    Mode_FlyUpWind = 1
    Mode_CastForOdor = 2
    Mode_Trapped = 3


    def __init__(self,param={}): 
        self.param = dict(self.DefaultParam)
        self.param.update(param)
        self.check_param()

        self.x_position = self.param['x_start_position']
        self.y_position = self.param['y_start_position']
        self.x_velocity = self.param['flight_speed']*scipy.cos(self.param['initial_heading'])
        self.y_velocity = self.param['flight_speed']*scipy.sin(self.param['initial_heading'])

        self.mode = scipy.full((self.size,), self.Mode_FixHeading, dtype=int)
        self.heading_error = scipy.zeros((self.size,)) 
        self.t_last_cast = scipy.zeros((self.size,)) 

        cast_interval = self.param['cast_interval']
        self.dt_next_cast = scipy.random.uniform(cast_interval[0], cast_interval[0], (self.size,))
        self.cast_sign = scipy.random.choice([-1,1],(self.size,))

        self.in_trap = scipy.full((self.size,), False, dtype=bool)
        self.trap_num = scipy.full((self.size,),-1, dtype=int)
        self.x_trap_loc = scipy.zeros((self.size,))
        self.y_trap_loc = scipy.zeros((self.size,))
        self.t_in_trap = scipy.zeros((self.size,))


    def check_param(self): 
        """
        Check parameters - mostly just that shape of ndarrays match 
        """
        if scipy.ndim(self.param['initial_heading'].shape) > 1:
            raise(ValueError, 'initial_heading must have ndim=1')

        equal_shape_list = ['x_start_position','y_start_position','flight_speed','release_time']
        for item in equal_shape_list:
            if self.param[item].shape != self.param['initial_heading'].shape:
                raise(ValueError, '{0}.shape must equal initial_heading.shape'.format(item))


    @property
    def size(self):
        return self.param['initial_heading'].shape[0]


    def update(self, t, dt, wind_field, odor_field):
        """
        Update fly swarm one time step. 
        """

        # Get masks for selecting fly based on mode
        mask_release = t > self.param['release_time'] 
        mask_fixhead = mask_release & (self.mode == self.Mode_FixHeading)
        mask_flyupwd = mask_release & (self.mode == self.Mode_FlyUpWind)
        mask_castfor = mask_release & (self.mode == self.Mode_CastForOdor)

        # Get odor value and wind vectors at current position and time
        odor = odor_field.value(t,self.x_position,self.y_position)
        x_wind, y_wind = wind_field.value(t,self.x_position, self.y_position)
        x_wind_unit, y_wind_unit = unit_vector(x_wind, y_wind)
        wind_uvecs = {'x': x_wind_unit,'y': y_wind_unit} 

        # Update state for flies detectoring odor plumes
        masks = {'fixhead': mask_fixhead, 'castfor': mask_castfor}
        self.update_for_odor_detection(dt, odor, wind_uvecs, masks)

        # Update state for files losing odor plume or already casting.  
        masks = {'flyupwd': mask_flyupwd, 'castfor': mask_castfor}
        self.update_for_odor_loss(t, dt, odor, wind_uvecs, masks)

        # Udate state for flies in traps
        self.update_for_in_trap(t, odor_field)

        # Update position based on mode and current velocities
        mask_trapped = self.mode == self.Mode_Trapped
        mask_move = mask_release & (~mask_trapped)
        self.x_position[mask_move] += dt*self.x_velocity[mask_move] 
        self.x_position[mask_move] += dt*self.param['wind_slippage']*x_wind[mask_move]
        self.y_position[mask_move] += dt*self.y_velocity[mask_move] 
        self.y_position[mask_move] += dt*self.param['wind_slippage']*y_wind[mask_move]


    def update_for_odor_detection(self, dt, odor, wind_uvecs, masks):
        """
         Update simulation for odor detection 
         * Find flies in FixHeading and CastForOdor modes where the odor value >= upper threshold.  
         * Test if they detect odor (roll dice and compare with dection probabilty).  
         * If they do detect odor change their  mode to FlyUpWind.
         * set x and y velocities to upwind at speed
        """
        x_wind_unit = wind_uvecs['x']
        y_wind_unit = wind_uvecs['y']
        mask_fixhead = masks['fixhead']
        mask_castfor = masks['castfor']

        mask_gt_upper = odor >= self.param['odor_thresholds']['upper'] 
        mask_candidates = mask_gt_upper & (mask_fixhead | mask_castfor)
        dice_roll = scipy.full((self.size,),scipy.inf)
        dice_roll[mask_candidates] = scipy.rand(mask_candidates.sum())

        # Convert probabilty/sec to probabilty for time step interval dt
        odor_probability_upper = 1.0 - (1.0 - self.param['odor_probabilities']['upper'])**dt
        mask_change = dice_roll < odor_probability_upper 
        self.mode[mask_change] = self.Mode_FlyUpWind

        # Compute new heading error for flies which change mode
        heading_error_std = self.param['heading_error_std']
        self.heading_error[mask_change] = heading_error_std*scipy.randn(mask_change.sum())

        # Set x and y velocities for the flies which just changed to FlyUpWind.
        x_unit_change, y_unit_change = rotate_vecs(
                x_wind_unit[mask_change],
                y_wind_unit[mask_change],
                self.heading_error[mask_change]
                )
        speed = self.param['flight_speed'][mask_change]
        self.x_velocity[mask_change] = -speed*x_unit_change
        self.y_velocity[mask_change] = -speed*y_unit_change

    def update_for_odor_loss(self, t, dt, odor, wind_uvecs, masks):
        """
         Update simulation for flies which lose odor or have lost odor and are
         casting. 
         * Find flies in FlyUpWind mode where the odor value <= lower threshold.  
         * Test if they lose odor (roll dice and compare with probabilty).  
         * If they lose odor change mode to CastForOdor.
         * Update velocties for flies in CastForOdor mode.
        """

        x_wind_unit = wind_uvecs['x']
        y_wind_unit = wind_uvecs['y']
        mask_flyupwd = masks['flyupwd']
        mask_castfor = masks['castfor']

        mask_lt_lower = odor <= self.param['odor_thresholds']['lower']
        mask_candidates = mask_lt_lower & mask_flyupwd
        dice_roll = scipy.full((self.size,),scipy.inf)
        dice_roll[mask_candidates] = scipy.rand(mask_candidates.sum())

        # Convert probabilty/sec to probabilty for time step interval dt
        odor_probability_lower = 1.0 - (1.0 - self.param['odor_probabilities']['lower'])**dt
        mask_change = dice_roll < odor_probability_lower 
        self.mode[mask_change] = self.Mode_CastForOdor

        # Lump together flies changing to CastForOdor mode with casting flies which are
        # changing direction (e.g. time to make cast direction change) 
        mask_change |= mask_castfor & (t > (self.t_last_cast + self.dt_next_cast))

        # Computer new heading errors for flies which change mode
        self.heading_error[mask_change] = self.param['heading_error_std']*scipy.randn(mask_change.sum())

        # Set new cast intervals and directions for flies chaning to CastForOdor or starting a new cast
        cast_interval = self.param['cast_interval']
        self.dt_next_cast[mask_change] = scipy.random.uniform(
                cast_interval[0], 
                cast_interval[0], 
                (mask_change.sum(),)
                )
        self.t_last_cast[mask_change] = t
        self.cast_sign[mask_change] = scipy.random.choice([-1,1],(mask_change.sum(),))

        # Set x and y velocities for new CastForOdor flies
        x_unit_change, y_unit_change = rotate_vecs(
                x_wind_unit[mask_change],
               -y_wind_unit[mask_change],
                self.heading_error[mask_change]
                )
        speed = self.param['flight_speed'][mask_change]
        self.x_velocity[mask_change] = self.cast_sign[mask_change]*speed*x_unit_change
        self.y_velocity[mask_change] = self.cast_sign[mask_change]*speed*y_unit_change


    def update_for_in_trap(self, t, odor_field):
        """
         Update simulation for flies in traps. 
         * If flies are in traps. If so record trap info and time.  
        """
        for trap_num, trap_loc in enumerate(odor_field.param['source_locations']):
            dist_vals = distance((self.x_position, self.y_position),trap_loc)
            mask_trapped = dist_vals < odor_field.param['trap_radius']
            self.mode[mask_trapped] = self.Mode_Trapped
            self.trap_num[mask_trapped] = trap_num 
            self.x_trap_loc[mask_trapped] = trap_loc[0]
            self.y_trap_loc[mask_trapped] = trap_loc[1]
            self.x_velocity[mask_trapped] = 0.0
            self.y_velocity[mask_trapped] = 0.0




