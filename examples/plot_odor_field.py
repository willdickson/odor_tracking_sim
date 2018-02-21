import scipy
import matplotlib.pyplot as plt

import odor_tracking_sim.wind_models as wind_models
import odor_tracking_sim.odor_models as odor_models
import odor_tracking_sim.utility as utility


# Source location and strength
number_sources = 6
radius_sources = 1000.0 
strength_sources = 10.0
location_list, strength_list = utility.create_circle_of_sources(
        number_sources,
        radius_sources,
        strength_sources
        )

# Create constant wind field
wind_param = {
        'speed': 0.2,
        'angle': 45.0*scipy.pi/180.0,
        }
wind_field = wind_models.ConstantWindField(param=wind_param)

# Create scalar odor concentration field
odor_param = {
        'wind_field'       : wind_field, 
        'diffusion_coeff'  : 0.01,
        'source_locations' : location_list, 
        'source_strengths' : strength_list,
        'epsilon'          : 0.01,
        'trap_radius'      : 100.0
        }
odor_field = odor_models.FakeDiffusionOdorField(odor_param)

scale = 2.0
plot_size= scale*radius_sources
plot_param = { 
        'xlim' : (-plot_size, plot_size),
        'ylim' : (-plot_size, plot_size),
        'xnum' : 500,
        'ynum' : 500,
        'cmap' : 'binary',
        #'threshold': 0.001,
        }
odor_field.plot(plot_param=plot_param)
plt.show()
