import os
from time import time

import argparse
import numpy as np
# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from gym.utils.env_checker import check_env
from gym.wrappers import FlattenObservation
from stable_baselines3.common.monitor import Monitor
from stable_baselines3 import DQN, PPO, TD3
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback
from stable_baselines3.common.noise import NormalActionNoise

from mec_moba.drlalgo.ddqn import DDQN
from mec_moba.envs import MecMobaDQNEvn
from mec_moba.envs.mec_moba_cont_act_env import MecMobaContinuosActionEvn


def parse_cli_args():
    parser = argparse.ArgumentParser(description="DRL MOBA on Stable Baseline 3")
    parser.add_argument('--train-epochs', type=int, default=52 * 10, help="Number of training weeks")
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--seed', type=int, required=False, default=None)
    dqn_grp_parser = parser.add_argument_group('DQN')
    dqn_grp_parser.add_argument('--dqn-batch-size', default=32, type=int)
    dqn_grp_parser.add_argument('--dqn-buffer-size', default=100_000, type=int)
    dqn_grp_parser.add_argument('--dqn-final-epsilon', default=0.05, type=float)
    dqn_grp_parser.add_argument('--dqn-learning-starts', default=5000)
    dqn_grp_parser.add_argument('--dqn-exploration_fraction', default=0.1)

    resume_evaluate_mtx_grp = parser.add_mutually_exclusive_group()
    resume_evaluate_mtx_grp.add_argument('--resume', action='store_true')
    resume_evaluate_mtx_grp.add_argument('--evaluate', action='store_true')

    return parser.parse_args()


def main(cli_args):
    # log_dir = "./tmp/gym/{}".format(int(time()))
    # os.makedirs(log_dir, exist_ok=True)

    env = MecMobaContinuosActionEvn(reward_weights=(0.5, 0.5, 1), normalize_reward=True)
    env = FlattenObservation(env)
    # check_env(env, warn=True)

    learn_weeks = 52 * 100
    save_freq_steps = 1008 * 52

    checkpoint_callback = CheckpointCallback(save_freq=save_freq_steps, save_path='./logs/',
                                             name_prefix='rl_mlp_model_test')

    # model = DDQN('MlpPolicy', env,
    #              verbose=1,
    #              learning_starts=100,
    #              buffer_size=100_000,
    #              target_update_interval=2000,
    #              #tau=0.001,
    #              exploration_fraction=0.7,
    #              exploration_final_eps=0.02,
    #              batch_size=256,
    #              policy_kwargs={'net_arch': [64,64,64]},
    #              tensorboard_log="./tb_log/dqn_mec_moba_tensorboard/")
    n_actions = env.action_space.shape[-1]
    action_noise = NormalActionNoise(mean=np.zeros(n_actions), sigma=0.1 * np.ones(n_actions))
    model = TD3("MlpPolicy", env,
                action_noise=action_noise,
                buffer_size=100_000,
                batch_size=500,
                learning_starts=1000,
                learning_rate=1e-4,
                verbose=1,
                policy_kwargs={'net_arch': [64, 32, 16]},
                tensorboard_log="./tb_log/dqn_mec_moba_tensorboard/")

    # model = PPO('MlpPolicy', env, verbose=1, n_steps=500, batch_size=50,
    #             vf_coef=0.5, ent_coef=0.01, tensorboard_log="./tb_log/ppo_mec_moba_tensorboard/")
    model.set_random_seed(1000)
    model.learn(total_timesteps=1008 * learn_weeks, callback=checkpoint_callback)

    # obs = env.reset()
    # for i in range(1000):
    #     action, _state = model.predict(obs, deterministic=True)
    #     print(action)
    #     obs, reward, done, info = env.step(action)
    #     env.render()
    #     if done:
    #         obs = env.reset()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main(cli_args=parse_cli_args())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
