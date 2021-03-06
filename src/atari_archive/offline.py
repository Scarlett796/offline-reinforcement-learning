import gym
import yaml
from tqdm import tqdm
import numpy as np
import torch
from torch.utils.data import DataLoader
from src.atari_archive.utils.data import EnvDataset, Summary
from src.atari_archive.utils.networks import ConvEncoder
from src.atari_archive.utils.preprocess import preprocess_state
from src.atari_archive.agents import OfflineDQNAgent


def main():
    with open('config.yml', 'r') as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.FullLoader)
    train(cfg)


def train(cfg: dict):
    print('Loading environment {}.'.format(cfg['ATARI_ENV']))
    env = gym.make(cfg['ATARI_ENV'])
    env.reset()
    observation_space = env.observation_space.shape
    action_space = 3
    action_map = {0: 0, 1: 2, 2: 3}
    state = torch.zeros((1, 16))

    print('Creating Agent.')
    agent = OfflineDQNAgent(observation_space, action_space)
    summary = Summary(cfg['SUMMARY_PATH'], agent.name)
    agent.print_model()
    agent.add_summary_writer(summary)

    print('Initializing Dataloader.')
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print('Utilizing device {}'.format(device))
    training_data = EnvDataset(cfg['TRAIN_DATA_PATH'])
    data_loader = DataLoader(dataset=training_data,
                             batch_size=cfg['BATCH_SIZE'],
                             shuffle=True,
                             num_workers=4,
                             pin_memory=True)

    print('Initializing Encoder.')
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    encoder = ConvEncoder()
    encoder.load_state_dict(torch.load(cfg['AUTO_SAVE_PATH'] + '/encoder.pt',
                                       map_location=device))
    encoder.to(device)
    encoder.eval()

    print('Start training with {} epochs'.format(cfg['EPOCHS']))
    for e in range(1, cfg['EPOCHS'] + 1):
        for i_batch, sample_batched in enumerate(tqdm(data_loader)):
            agent.learn(sample_batched)

            summary.adv_step()

        rewards = []
        mean_reward = []
        counter = 0
        while counter < cfg['EVAL_EPISODES']:
            action = agent.act(state)

            if cfg['EVAL_RENDER']:
                env.render()

            state, reward, done, _ = env.step(action_map[int(action)])
            state = preprocess_state(state).to(device)
            state, _, _ = encoder.encode(state)

            rewards.append(reward)
            if done:
                env.reset()
                mean_reward.append(sum(rewards))
                rewards = []
                counter += 1

        agent.save(e)
        summary.add_scalar('Episode Reward', np.mean(mean_reward))
        summary.adv_episode()
        summary.writer.flush()

    print('Closing environment.')
    env.close()


if __name__ == '__main__':
    main()
