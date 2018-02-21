import scipy
import math
import matplotlib.pyplot as plt
import cPickle as pickle

input_file = 'swarm_data.pkl'

with open(input_file,'r') as f:
    swarm = pickle.load(f)


num_bins = 20

trap_num_list = swarm.get_trap_nums()

plt.figure(1)
t = swarm.get_time_trapped()

plt.hist(t,num_bins)
plt.xlabel('(s)')
plt.ylabel('count')
plt.title('time trapped (all traps)')

plt.figure(2)
for i,num in enumerate(trap_num_list):
    plt.subplot(math.ceil(len(trap_num_list)/2),2,i+1)
    t = swarm.get_time_trapped(num)
    plt.hist(t,num_bins)
    plt.xlabel('(s)')
    plt.ylabel('trap:{0}'.format(num))
    #plt.title('time trapped, trap_num = {0}'.format(num))

plt.show()
