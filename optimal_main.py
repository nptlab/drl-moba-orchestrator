import os
import numpy as np
import json
# from data.probability_extractor import *
# from data.delay_exctractor import *
# from data.user_home_extractor import *
from mec_moba.environment.utils.delay_exctractor import *
import gurobipy as gp
import math
import csv
import itertools
import pickle

from mec_moba.environment.matches import GameGenerator


def compute_optimal_solution(seed):
    T_SLOTS = 144
    T = T_SLOTS + 6 * 12
    F = 7
    MATCH_DURATION = 10
    SEED = seed
    # N = int(3500 / 7)

    game_generator = GameGenerator()
    game_generator.set_seed(SEED)
    game_generator.generate_epoch_matches()

    request_time_sigma = []
    games = []
    for t_slot in range(T_SLOTS):
        for g in game_generator.get_match_requests(t_slot):
            games.append(g)  # .compute_QoS()
            request_time_sigma.append(t_slot)

    print(len(games))
    os.makedirs(f'logs/{SEED}', exist_ok=True)
    os.makedirs(f'logs/{SEED}/opt', exist_ok=True)

    pickle.dump([g.to_dict() for g in games], open(f'logs/{SEED}/games.pkl', 'wb'))

    N = len(games)

    print(N, F, T)

    cost_c = np.zeros((N, F, T))

    # extract_delay()
    info_physical_net = extract_delay()
    delay_dict = info_physical_net['delays']

    for n in range(N):
        for f in range(F):
            for t in range(T):
                # fps = round(1000 / max([(delay_dict[(t % 1008, bs[0], f)]) for bs in game_index[n]]))
                # self.delay_dict[(self.environment.epoch_t_slot, bs, mec)]
                rtt = max(delay_dict[t, bs, f] for bs in games[n].get_base_stations())
                cost_c[n, f, t] = 5 - games[n].compute_QoS(rtt)

    # [x for x in game_request_timeslot_sample]
    delta = MATCH_DURATION
    w = np.zeros((N, T))
    for n in range(N):
        for t in range(T):
            w[n, t] = max(0, t - request_time_sigma[n])

    # Create a new model
    m = gp.Model("DQN")
    m.Params.LogToConsole = 1
    m.Params.MIPGap = 0.001
    m.Params.TimeLimit = 3000

    # Create variables
    x = m.addMVar((N, F, T), vtype=gp.GRB.BINARY, name="X")
    v = m.addMVar((F, T), lb=0, vtype=gp.GRB.INTEGER, name="v")
    y = m.addMVar((N, T), vtype=gp.GRB.BINARY, name="Y")
    s = m.addMVar((N, T), vtype=gp.GRB.BINARY, name="S")

    # Set objective
    m.setObjective(sum(sum(sum([cost_c[i, j, t] * x[i, j, t] for j in range(F)]) for i in range(N)) for t in range(T))
                   + sum(sum([1 * v[j, t] for j in range(F)]) for t in range(T))
                   + sum(sum([1 * y[i, t] for i in range(N)]) for t in range(T))
                   + sum(sum(w[i, t] * s[i, t] for i in range(N)) for t in range(T)),
                   gp.GRB.MINIMIZE)

    # Set constrains

    #
    m.addConstrs(
        (sum([x[i, j, t] for j in range(F)]) == sum([s[i, _t] for _t in range(max(0, t - delta), t)]) for i in range(N) for t in range(T)),
        name='c0')

    #
    m.addConstrs((sum([s[i, t] for t in range(request_time_sigma[i], T)]) == 1 for i in range(N)),
                 name='c1')

    m.addConstrs((sum([s[i, t] for t in range(0, request_time_sigma[i])]) == 0 for i in range(N)),
                 name='c1_2')
    #
    m.addConstrs(((x[i, j, t + 1] - x[i, j, t] <= y[i, t]) for i in range(N) for j in range(F) for t in range(T - 1)),
                 name='c2')

    #
    m.addConstrs(((sum([x[i, j, t] for i in range(N)]) <= 8 + v[j, t]) for j in range(F) for t in range(T)),
                 name='c3')

    m.addConstrs(((v[j, t] <= 4) for j in range(F) for t in range(T)),
                 name='c4')

    m.update()
    m.optimize()

    # print('Obj: %g' % m.objVal)
    # print(v_ret)
    if not hasattr(m, 'objVal'):
        print('no solution gurobi, there is a None Type')

    else:
        print('success', m.objVal)
        with open(f'logs/{SEED}/opt/x.csv', 'w', newline='') as fd:
            writer = csv.writer(fd)
            for t in range(T):
                for j in range(F):
                    for i in range(N):
                        if x[i][j][t].x > 0:
                            writer.writerow([t, j, i, x[i][j][t].x])

        with open(f'logs/{SEED}/opt/s.csv', 'w', newline='') as fd:
            writer = csv.writer(fd)
            for t in range(T):
                for i in range(N):
                    if s[i, t].x > 0:
                        writer.writerow([t, i, s[i, t].x])

    with open(f'logs/{SEED}/opt/sigma.csv', 'w', newline='') as f_d:
        writer = csv.writer(f_d)
        writer.writerows([[i, request_time_sigma[i]] for i in range(len(request_time_sigma))])


if __name__ == '__main__':
    for seed in [1000, 2000, 3000]:
        compute_optimal_solution(seed)