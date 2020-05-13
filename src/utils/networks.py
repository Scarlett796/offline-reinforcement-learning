from torch import nn


class DQN(nn.Module):

    def __init__(self, observation_space, action_space):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(in_features=observation_space, out_features=128)
        self.bn1 = nn.LayerNorm(128)
        self.fc2 = nn.Linear(in_features=128, out_features=32)
        self.bn2 = nn.LayerNorm(32)
        self.fc3 = nn.Linear(in_features=32, out_features=action_space)

        self.elu = nn.ELU()

    def forward(self, x):
        x = self.fc1(x)
        x = self.bn1(x)
        x = self.elu(x)
        x = self.fc2(x)
        x = self.bn2(x)
        x = self.elu(x)
        x = self.fc3(x)
        return x


class DQNCNN(nn.Module):

    def __init__(self, observation_space, action_space):
        super(DQNCNN, self).__init__()
        input_height = observation_space[0]
        input_width = observation_space[1]
        input_channel = observation_space[2]

        kernel_size = [8, 4]
        stride = [4, 2]

        self.conv1 = nn.Conv2d(input_channel, 16, kernel_size=kernel_size[0], stride=stride[0])
        self.conv2 = nn.Conv2d(16, 32, kernel_size=kernel_size[1], stride=stride[1])

        def size_out(size, kernel_size, stride):
            return (size - (kernel_size - 1) - 1) // stride + 1

        conv_w = size_out(size_out(input_height, kernel_size[0], stride[0]), kernel_size[1], stride[1])
        conv_h = size_out(size_out(input_width, kernel_size[0], stride[0]), kernel_size[1], stride[1])
        linear_input_size = conv_w * conv_h * 32
        self.fc1 = nn.Linear(linear_input_size, 256)
        self.out = nn.Linear(256, action_space)

        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.conv1(x)
        x = self.relu(x)
        x = self.conv2(x)
        x = self.relu(x)
        x = self.fc1(x.view(x.size(0), -1))
        x = self.relu(x)
        x = self.out(x)
        return x
