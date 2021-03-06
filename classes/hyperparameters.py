#own imports
from convnet3d import relu
from numpy import float32, random, floor
from glob import glob

# hyper parameters
# ------------------------------------------------------------------------------

class files:
    """
    files to define the file location and relevant info.
    """
    def __init__(self, src):
        self.train = glob(src+'/train/batch_*.zip')#+glob(src+'/valid/batch_100_*.zip')
        self.valid = glob(src+'/valid/batch_*.zip')#[:2]
        self.test = glob(src+'/train/batch_*.zip')#[:2]
        self.n_train = len(self.train) 
        self.n_valid = len(self.valid)
        self.n_test = len(self.test)

# use techniques/methods
class use:
    drop = True # dropout
    depth = True # use depth map as input
    aug = False # data augmentation
    load = False # load params.p file
    load_params_pos = 0
    valid2 = False
    fast_conv = False
    norm_div = False
    maxout = False
    norm = True # normalization layer
    mom = True # momentum

# learning rate
class lr:
    init = 3e-3 # lr initial value
    decay = .95 # lr := lr*decay
    decay_big = .1
    decay_each_epoch = True
    decay_if_plateau = True

class batch:
    mini = 64 # number of samples before updating params
    micro = 64  # number of samples that fits in memory
    batch_size = 32 #batch size (wudi added this orthodox parameter)

# regularization
class reg:
    L1_vid = .0 # degree/amount of regularization
    L2_vid = .0 # 1: only L1, 0: only L2

# momentum
class mom:
    momentum = .9 # momentum value
    nag = True # use nesterov momentum

# training
class tr:
    n_epochs = 1000 # number of epochs to train
    patience = 1 # number of unimproved epochs before decaying learning rate
    batch_size = 1024 # batchsize --should be strictly no larger than 1000!!! LIO care--because
                        # during preprocessing, wudi make a batch if number of frames reach 1000!
    in_shape = (batch_size,2,2,4,64,64) # (batchsize, gray/depth, body/hands, frames, w, h) input video shapes 
    rng = random.RandomState(1337) # this will make sure results are always the same
    first_report = True # report timing if first report
    moved = False
    inspect = True # inspection for gradient
    video_shapes = [in_shape[-3:]]

# dropout
class drop:
    p_vid_val = float32(0.5) # dropout on vid
    p_hidden_val = float32(0.5) # dropout on hidden units

class net:
    shared_stages = [] # stages where weights are shared
    shared_convnets = [] # convnets that share weights ith neighbouring convnet
    n_convnets = 2 # number of convolutional networks in the architecture
    # maps = [2,16,32,48] # feature maps in each convolutional network
    maps = [2,32,64,64] # feature maps in each convolutional network

    # kernels = [(1,7,7), (1,8,8), (1,6,6)] # convolution kernel shapes
    # pools = [(2,2,2), (2,2,2), (2,2,2)] # pool/subsampling shapes

    # kernels = [(1,5,5), (1,5,5), (1,5,5)] # convolution kernel shapes
    # pools = [(2,2,2), (2,2,2), (2,3,3)] # pool/subsampling shapes

    # kernels = [(1,9,9), (1,5,5), (1,3,3)] # convolution kernel shapes
    # pools = [(2,2,2), (2,2,2), (2,2,2)] # pool/subsampling shapes

    # kernels = [(1,9,9), (1,5,5), (1,3,3)] # convolution kernel shapes
    # pools = [(2,2,2), (2,2,2), (2,5,5)] # pool/subsampling shapes

    kernels = [(1,5,5), (1,5,5), (1,4,4)] # convolution kernel shapes
    pools = [(2,2,2), (2,2,2), (1,2,2)] # pool/subsampling shapes

    W_scale = [[0.01,0.01],[0.01,0.01],[0.01,0.01],0.01,0.01]
    b_scale = [[0.1,0.1],[0.1,0.1],[0.1,0.1],0.1,0.1]
    # scaler = [[33,24],[7.58,7.14],[5,5],1,1]
    scaler = [[1,1],[1,1],[1,1],1,1]
    stride = [1,1,1]
    hidden_traj = 64 # hidden units in MLP
    hidden_vid = 1024 # hidden units in MLP
    norm_method = "lcn" # normalisation method: lcn = local contrast normalisation
    pool_method = "max" # maxpool
    fusion = "early" # early or late fusion
    hidden = hidden_traj+hidden_vid if fusion=="late" else 1024 # hidden units in MLP
    STATE_NO = 5
    n_class = STATE_NO * 20 + 1
    n_stages = len(kernels)
    activation = "relu" # tanh, sigmoid, relu, softplus

class DataLoader():
    def __init__(self, src, batch_size):
        self.batch_size = batch_size
        import h5py
        file = h5py.File(src+"/data%d.hdf5", "r", driver="family", memb_size=2**32-1)
        self.x_train = file["x_train"]
        self.x_valid = file["x_valid"]
        self.y_train = file["y_train"]
        self.y_valid = file["y_valid"]

        self.n_iter_train = int(floor(self.x_train.shape[0]/float(batch_size)))
        self.n_iter_valid = int(floor(self.x_valid.shape[0]/float(batch_size)))

        self.shuffle_train()
        self.shuffle_valid()

    def next_train_batch(self, x_, y_):
        if len(self.pos_train) == 0: self.shuffle_train()
        pos = self.pos_train.pop()
        x_.set_value(self.x_train[pos:pos+self.batch_size] , borrow=True)
        y_.set_value(self.y_train[pos:pos+self.batch_size] , borrow=True)

    def next_valid_batch(self, x_, y_):
        if len(self.pos_valid) == 0: self.shuffle_valid()
        pos = self.pos_valid.pop()
        x_.set_value(self.x_valid[pos:pos+self.batch_size] , borrow=True)
        y_.set_value(self.y_valid[pos:pos+self.batch_size] , borrow=True)

    def shuffle_train(self):
        self.pos_train = list(random.permutation(self.n_iter_train)*self.batch_size)

    def shuffle_valid(self):
        self.pos_valid = list(random.permutation(self.n_iter_valid)*self.batch_size)

