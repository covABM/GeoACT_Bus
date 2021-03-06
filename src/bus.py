# imports
import numpy as np
import pandas as pd
import math
from scipy import stats
import sys
import json
import os
import matplotlib.pyplot as plt

# import from infection.py
from infection import generate_infectivity_curves, plot_infectivity_curves, return_aerosol_transmission_rate

def load_parameters(filepath):
    '''
    Loads input and output directories
    '''
    try:
        with open(filepath) as fp:
            parameter = json.load(fp)
    except:
        try:
            with open('../' + filepath) as fp:
                parameter = json.load(fp)
        except:
            with open('../../' + filepath) as fp:
                parameter = json.load(fp)

    return parameter

#
bus_flow_pos = load_parameters('config/f_seating_full.json')
bus_edge_pos = load_parameters('config/f_seating_half_edge.json')
bus_zig_pos = load_parameters('config/f_seating_half_zig.json')
#
aerosol_params = load_parameters('results/aerosol_data_.json')
dp = load_parameters('results/default_data_.json')
select_dict = load_parameters('config/neighbor_logic.json')


def get_distance_bus(student_pos, this_id, initial_id):
    x1, y1 = student_pos[initial_id]
    x2, y2 = student_pos[this_id]
    return x1, x2, y1, y2

def get_incoming(x, y, old):
    neighb = []
    count = 0
    x_max = old.shape[0] - 1
    y_max = old.shape[1] - 1

    if x == 0:
        x_range = [0, 1]
    elif x == x_max:
        x_range = [-1, 0]
    else:
        x_range = [-1, 0, 1]

    if y == 0:
        y_range = [0, 1]
    elif y == y_max:
        y_range = [-1, 0]
    else:
        y_range = [-1, 0, 1]

    this_val = old[x][y]
    this_direction = bus_flow_direction[x][y]
    this_velocity = bus_flow_velocity[x][y]

    dict_iterate_count = 0
    for i in x_range:
        for j in y_range:
            dict_iterate_count += 1
            if i == 0 and j == 0:
                # disperse .1 to all 8 neighboring squares
                for x_ in x_range:
                    for y_ in y_range:
                        direction = bus_flow_direction[x_][y_]
                        if direction in select_dict[str([i, j])]:
                            idx = select_dict[str([i, j])].index(direction)
                            vel_idx = bus_flow_velocity[x + i][y + j]
                            magnitude = .1
                            value = old[x + i][y + j]
                            neighb.append(value * magnitude)

            else:
                # factors in neighboring cell
                direction = bus_flow_direction[x + i][y + j]
                # update direction function

                if direction in select_dict[str([i, j])]:
                    idx = select_dict[str([i, j])].index(direction)
                    vel_idx = bus_flow_velocity[x + i][y + j]
                    magnitude = select_dict["mag_array"][vel_idx] * select_dict["risk_array"][idx]
                    value = old[x + i][y + j]
                    neighb.append(value * magnitude)
                # else nothing moves in

    if len(neighb) > 0: # replaces self.value
        new_val = this_val * (1 - .5 * this_velocity) + np.mean(neighb)
    else:
        new_val = this_val
    return new_val

def air_effects(i, j, oldQ):
    '''
    i, j: x y locations

    oldQ: old quanta at that cube

    get neighbors directions and magnitude
    determine % in and % out
    '''
    # windows
    if j < 2 or j > 4:
        new = oldQ * .85

    # ceiling vents
    if (i > 6 and i < 9) or (i > 12 and i < 15):
        new = oldQ * .6
    else:
        new = .9 * oldQ
    return new

def make_new_heat(old, bus_flow_pos, init_infected_ = None):
    '''
    1 minute step used to calculate concentration_distribution iteratively
    '''
    if init_infected_:
        pass
    else:
        init_infected_ = np.random.choice(list(bus_flow_pos.keys()))

    initial_loc = bus_flow_pos[init_infected_]
    new = old.copy()
    out = old.copy()
    # spatial
    for i in range(len(old)):
        for j in range(len(old[i])):
            dist = math.sqrt(((initial_loc[0] - i)**2) + (initial_loc[1] - j)**2)
            new_val = old[i][j] + (1/(2.02 ** dist)) # 1 quanta per step by distance
            new[i][j] = new_val

            ##################################################
    for i in range(len(new)):
        for j in range(len(new[i])):
            neighbor_val = get_incoming(i, j, new)
            air_val = air_effects(i, j, neighbor_val)
            out[i][j] = air_val  # +=???
    return out, init_infected_

bus_flow_direction = np.array([[1, 1, 1, 2, 3, 4, 4],
              [1, 4, 7, 8, 9, 9, 6],
              [4, 7, 7, 8, 9, 9, 6],
              [4, 4, 5, 2, 5, 4, 4],
              [8, 5, 5, 2, 5, 5, 8], #
              [1, 1, 1, 2, 5, 6, 6],
              [1, 1, 2, 2, 5, 6, 6],
              [1, 1, 2, 2, 3, 3, 6],
              [5, 5, 5, 2, 5, 5, 5],
              [1, 1, 1, 2, 3, 3, 3], #
              [1, 1, 2, 2, 2, 3, 3],
              [1, 1, 2, 2, 2, 3, 3],
              [1, 1, 2, 2, 2, 3, 3],
              [1, 1, 2, 2, 2, 3, 3],
              [1, 5, 5, 2, 2, 3, 3], #
              [1, 1, 1, 2, 2, 3, 3],
              [1, 1, 1, 2, 2, 3, 3],
              [1, 1, 1, 2, 3, 6, 6],
              [1, 1, 2, 2, 3, 3, 6],
              [1, 2, 2, 2, 3, 3, 6], #
              [4, 4, 4, 5, 6, 6, 6],
              [2, 2, 2, 5, 5, 5, 5],
              [2, 2, 5, 8, 2, 2, 2]])
bus_flow_velocity = np.array([[3,3,2,1,1,0,1],
    [1,0,1,2,3,2,2],
    [1,2,1,0,1,2,2],
    [2,1,0,0,0,1,1],
    [2,1,0,0,0,1,1], #
    [2,1,0,0,0,0,1],
    [1,1,0,0,0,0,1],
    [1,2,1,1,0,0,0],
    [0,1,2,1,0,1,2],
    [0,0,0,0,0,0,1], #
    [2,2,2,2,2,1,1],
    [3,2,2,2,2,2,2],
    [2,0,0,0,0,1,2],
    [1,2,2,2,2,2,1],
    [1,1,2,2,2,1,1], #
    [1,1,2,2,2,1,1],
    [1,1,1,1,1,1,1],
    [2,2,2,2,2,2,2],
    [2,2,3,3,3,2,2],
    [1,1,2,2,2,1,1], #
    [1,1,2,2,2,1,1],
    [1,1,1,1,1,1,1],
    [1,1,1,1,0,0,0],
    [1,1,0,0,0,0,0]])
#

def concentration_distribution(num_steps, num_sims, bus_flow_pos):
    '''
    Simulate distribution of concentration after
    30 steps
    100 runs
    random initial student/infectivity


    '''
    nothings = np.zeros(bus_flow_direction.shape)
    avg_array = nothings.copy()
    temp, initial = make_new_heat(nothings, bus_flow_pos, init_infected_=None)
    temp_array = []

    for step in range(num_steps):
        temp, initial = make_new_heat(temp, bus_flow_pos, init_infected_=initial)
        temp_array.append(temp)

    for i in range(len(temp_array)):
        # timesteps
        for y in range(len(temp_array[0])):
            for x in range(len(temp_array[0][0])):
                avg_array[y][x] += (temp_array[i][y][x] / len(temp_array))

    return temp_array, avg_array

def bus_sim(n_students, mask, n_sims, trip_len, flow_seats_, window_): # do 1 trip with given params
    '''
    in:
    mask %
    windows up / down
    students: 28 or 56

    '''
    if flow_seats_ == "full":
        seat_dict = load_parameters('config/f_seating_full.json')
    else:
        if flow_seats_ == "window":
            seat_dict = load_parameters('config/f_seating_half_edge.json')
        elif flow_seats_ == "zigzag":
            seat_dict = load_parameters('config/f_seating_half_zig.json')
        else:
            print('ERROR')
    flow_seating = {key: value for key, value in seat_dict.items() if int(key) < n_students}
    # initialize model run data storage
    who_infected_bus = {str(i): 0 for i in range(len(flow_seating.keys()))}
    init_inf_dict = {str(i): 0 for i in range(len(flow_seating.keys()))}
    n_steps = int(int(trip_len) / 5)
    transmission_bus_rates = {i: [] for i in flow_seating.keys()}
    temp_rates = {i: [] for i in flow_seating.keys()}
    averaged_all_runstep = {str(i): 0 for i in flow_seating.keys()}
    transmission_by_step = {str(i): [] for i in flow_seating.keys()}
    all_transmissions = []
    scatter_dist = {"distance": [], "transmission rate": []}
    infection_over_run = {str(i): 0 for i in range(len(flow_seating.keys()))}
    close_scatter_dist = {"distance": [], "transmission rate": []}
    far_scatter_dist = {"distance": [], "transmission rate": []}

    # get infective_df
    temp = generate_infectivity_curves()
    inf_df = plot_infectivity_curves(temp, plot= False)
    sls_symp_count, x_symp_count, s_l_s_infectivity_density, x_infectivity, distance_multiplier = temp
    l_shape, l_loc, l_scale = sls_symp_count
    g_shape, g_loc, g_scale = s_l_s_infectivity_density

    # print(dp, 'default')
    # print(window_, 'window var')#aerosol_params['floor_area'], aerosol_params['mean_ceiling_height'], aerosol_params['air_exchange_rate'], aerosol_params['aerosol_filtration_eff'], aerosol_params['relative_humidity'], aerosol_params['breathing_flow_rate'], aerosol_params['exhaled_air_inf'], aerosol_params['max_viral_deact_rate'], aerosol_params['mask_passage_prob'])


    bus_aerosol = return_aerosol_transmission_rate(window_)
    concentration_array, avg_matrix = concentration_distribution(n_steps, n_sims, bus_flow_pos)
    # return average concentration over run
    out_matrix = np.array(np.zeros(shape=concentration_array[0].shape))
    max_val = 0
    for conc in range(len(concentration_array)):
        for y in range(concentration_array[conc].shape[0]):
            for x in range(concentration_array[conc].shape[1]):
                out_matrix[y][x] += (concentration_array[conc][y][x] / len(concentration_array))
                if  (concentration_array[conc][y][x] / len(concentration_array)) > max_val:
                    max_val =  (concentration_array[conc][y][x] / len(concentration_array))

    concentration_ = out_matrix
    for conc in range(len(concentration_array)):
        for y in range(concentration_array[conc].shape[0]):
            for x in range(concentration_array[conc].shape[1]):
                if out_matrix[y][x] < 0:
                    out_matrix[y][x] = .0001
                else:
                    out_matrix[y][x] = out_matrix[y][x] / max_val

    # isn't

    # print(concentration_, 'concentration')
    run_average_array = []
    for run in range(n_sims):
        # initialize student by random selection# initial
        initial_inf_id = np.random.choice(list(who_infected_bus.keys()))
        init_inf_dict[initial_inf_id] += 1
        # initialize time until symptoms based on curve
        init_time_to_symp = int(np.round(stats.lognorm.rvs(l_shape, l_loc, l_scale, size=1)[0], 0))
        # fix overflow errors (unlikely but just in case)
        if init_time_to_symp >= 18:
            init_time_to_symp = 17
        if init_time_to_symp <= 0:
            init_time_to_symp = 0
        # initialize infectivity of student
        init_infectivity = inf_df.iloc[init_time_to_symp].gamma

        temp_average_array = temp_rates.copy()
        # print(temp_average_array)

        run_chance_of_0 = 1

        for step in range(n_steps): # infection calculated for 5-minute timesteps
            # bus trip 1way
            # iterate through students
            # print(seat_dict.keys())
            for student_id in flow_seating.keys():
                if student_id != initial_inf_id:
                    # masks wearing %
                    cwd = os.getcwd()
                    if isinstance(mask, str):
                        mask_ = int(mask.split('%')[0]) / 100
                        masks = np.random.choice([.1, 1], p=[mask_, 1-mask_])
                    else:
                        # print(mask, type(mask))
                        # m_var = mask / 100
                        masks = np.random.choice([.1, 1], p=[mask, 1-mask])

                    x1, x2, y1, y2 = get_distance_bus(flow_seating, student_id, initial_inf_id)
                    distance = math.sqrt(((.3 * (x2 - x1))**2)+((.3 * (y2-y1))**2))
                    chu_distance = 1 / (2.02 ** distance)

                    # for concentraion calculation
                    air_y, air_x = flow_seating[str(student_id)]
                    # print(student_id, 'id', air_x, air_y)
                    # print

                    # proxy for concentration
                    # print(out_matrix, 'out')
                    air_flow = out_matrix[round(air_y * 1.5 + 1)][air_x]

                    transmission = (init_infectivity * chu_distance * masks) + (air_flow * bus_aerosol)
                    # print(transmission)
                    # if transmission > 0.3:
                    #     # print(transmission)
                    #     # print('this is in case of calculation errors, shouldnt be printed')
                    #     transmission = .03
                        # print(air_flow, 'af')# * bus_aerosol)
                    # calculate transmissions
                    if np.random.choice([True, False], p=[transmission, 1-transmission]):
                        who_infected_bus[student_id] += 1
                    # if infected:
                    run_chance_of_0 *= (1-transmission)

                    # output temp is for each step
                    temp_average_array[student_id].append(transmission)
                    all_transmissions.append(transmission)
                    # print('oh')
                    # print(distance, 'd')
                    if distance < .5:
                        close_scatter_dist["distance"].append(distance)
                        close_scatter_dist["transmission rate"].append(transmission)
                    elif distance > 2:
                        far_scatter_dist["distance"].append(distance)
                        far_scatter_dist["transmission rate"].append(transmission)
                    else:
                        scatter_dist["distance"].append(distance)
                        scatter_dist["transmission rate"].append(transmission)

        run_average_array.append(1 - run_chance_of_0) # add chance of nonzero to array
        for id in flow_seating.keys():
            if len(temp_average_array[id]) > 0:
                transmission_by_step[id].append(np.mean(temp_average_array[id]))
            else:
                transmission_by_step[id].append(0)

    # takes average over all runs
    for id in flow_seating.keys():
        avg = np.mean(transmission_by_step[id])
        # print(avg, 'avg')
        averaged_all_runstep[id] = avg
        infection_over_run[id] = (1 - (1-avg)**n_steps)

    # print(close_scatter_dist)
    # average risk of >= 1 infection across all model runs
    if len(run_average_array) == 0:
        print('Sim failed')
    run_avg_nonzero = np.mean(run_average_array)
    # print('initially infected counts', init_inf_dict)
    # OUTPUT AVERAGE LIKELIHOOD OF >= 1 INFECTION
    # print(n_students)
    bus_out_array = [all_transmissions, averaged_all_runstep, infection_over_run, close_scatter_dist, scatter_dist, far_scatter_dist]
    # print(close_scatter_dist['distance'][:10])
    # print(far_scatter_dist['transmission rate'][:10])
    # print('lens', len(close_scatter_dist['distance']), len(scatter_dist['distance']), len(far_scatter_dist['distance']))
    return bus_out_array, concentration_array, out_matrix, run_avg_nonzero, concentration_ # added averaged concentration as avg_matrix
