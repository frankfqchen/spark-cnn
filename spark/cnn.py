import numpy as np
from time import time
from spark.conv import ConvolutionLayer
from spark.relu import ReLULayer
from spark.pool import PoolingLayer
from spark.fc import FCLayer
from spark.utils import *

class CNN():
    def __init__(self, I):
        self.name = 'cnn'
        self.I = I # I: number of iterations
        classifications = load_classifications()
        C = len(classifications)
        self.init_layers(C)
        self.C = C

        # hyper parameters settings
        self.rho = 0.01 # learning rate
        self.mu = 0.9 # momentum
        self.lam = 0.1 # regularization strength

        # logging settings
        self.verbose = False

    def init_layers(self, C):
        # initialize layers
        self.conv = ConvolutionLayer(64, 3, 1, 3, 1)
        self.relu = ReLULayer()
        self.pool = PoolingLayer(2, 2)
        self.fc = FCLayer(16, 16, 64, C)

    def train(self, size = 1000):
        X, Y = load_training_data(0, size)
        # input X images [N x W x H x D]
        # input Y labels [N]
        print('Start training CNN...')
        print('Training data size: %d' % size)

        time_begin = time()
        for i in range(0, self.I):
            print('iteration %d:' % i)

            # forward
            start = time()
            RS = self.forward(X)
            middle = time()

            # calculate loss and gradients
            L, dS = softmax(RS[3], Y) # get loss and gradients with softmax function

            # backward
            dAConv, dbConv, dAFC, dbFC = self.backward(X, RS, dS)
            end = time()

            # update parameters
            L = self.update(L, dAConv, dbConv, dAFC, dbFC)
            self.save()

            print('forward time %.3f, backward time %.3f, loss %.3f ' % \
                (middle - start, end - middle, L))

        # self.save()
        time_end = time()
        print('training done, total time consumption %.3f' % (time_end - time_begin))

    def forward(self, X):
        # X are the images [N x W x H x D]
        start = time()
        R1 = self.conv.forward(X) # result from conv layer
        end = time()
        if self.verbose:
            print('layer conv forward done: time %.3f' % (end - start))

        start = time()
        R2 = self.relu.forward(R1) # result from ReLU layer
        end = time()
        if self.verbose:
            print('layer relu forward done: time %.3f' % (end - start))

        start = time()
        R3 = self.pool.forward(R2) # result from pooling layer
        end = time()
        if self.verbose:
            print('layer pool forward done: time %.3f' % (end - start))

        start = time()
        R4 = self.fc.forward(R3) # result from fully connected layer
        end = time()
        if self.verbose:
            print('layer fc forward done: time %.3f' % (end - start))

        return [R1, R2, R3, R4]

    def backward(self, X, RS, dS):
        # X are the images [N x W x H x D]
        # Y are the correct labels [N x 1]
        # RS are results from forward run
        R1, R2, R3, R4 = RS

        start = time()
        dX, dAFC, dbFC = self.fc.backward(dS, R3)
        end = time()
        if self.verbose:
            print('layer fc backward done: time %.3f' % (end - start))

        start = time()
        dX = self.pool.backward(dX, R2)
        end = time()
        if self.verbose:
            print('layer pool backward done: time %.3f' % (end - start))

        start = time()
        dX = self.relu.backward(dX, R1)
        end = time()
        if self.verbose:
            print('layer relu backward done: time %.3f' % (end - start))

        start = time()
        dX, dAConv, dbConv = self.conv.backward(dX, X)
        end = time()
        if self.verbose:
            print('layer conv backward done: time %.3f' % (end - start))

        return dAConv, dbConv, dAFC, dbFC

    def update(self, L, dAConv, dbConv, dAFC, dbFC):
        # regularization
        L += 0.5 * self.lam * np.sum(self.conv.A * self.conv.A)
        L += 0.5 * self.lam * np.sum(self.fc.A * self.fc.A)
        dAFC += self.lam * self.fc.A
        dAConv += self.lam * self.conv.A

        # update neural network parameters
        # velocities
        self.conv.V = self.mu * self.conv.V - self.rho * dAConv
        self.fc.V = self.mu * self.fc.V - self.rho * dAFC
        # weights
        self.conv.A += self.conv.V
        self.fc.A += self.fc.V
        # biases
        self.conv.b += (0 - self.rho) * dbConv
        self.fc.b += (0 - self.rho) * dbFC

        return L

    def reload(self):
        # reload all layers' parameters
        self.conv.V = load_parameters_local(self.name + '_conv.V')
        self.conv.A = load_parameters_local(self.name + '_conv.A')
        self.conv.b = load_parameters_local(self.name + '_conv.b')
        self.fc.V = load_parameters_local(self.name + '_fc.V')
        self.fc.A = load_parameters_local(self.name + '_fc.A')
        self.fc.b = load_parameters_local(self.name + '_fc.b')

    def save(self):
        # save all layers' parameters
        save_parameters_local(self.name + '_conv.V', self.conv.V)
        save_parameters_local(self.name + '_conv.A', self.conv.A)
        save_parameters_local(self.name + '_conv.b', self.conv.b)
        save_parameters_local(self.name + '_fc.V', self.fc.V)
        save_parameters_local(self.name + '_fc.A', self.fc.A)
        save_parameters_local(self.name + '_fc.b', self.fc.b)

    def predict(self, X):
        # output predicted classifications
        self.reload()
        R1, R2, R3, R4 = self.forward(X)
        return R4
