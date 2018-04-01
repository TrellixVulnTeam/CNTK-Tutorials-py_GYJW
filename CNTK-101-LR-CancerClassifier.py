# https://cntk.ai/pythondocs/CNTK_101_LogisticRegression.html#Introduction
# ------Function------
# A cancer hospital has provided data and wants us to determine 
# if a patient has a fatal malignant cancer vs. a benign growth
# features: age and tumor size
# Author: wuyi
# Date: 2018-03-28--30
# 1.The model an be saved.

# Import the relevant componets
from __future__ import print_function
import numpy as np
import sys
import os

import cntk as C
import cntk.tests.test_utils # pytest is a python lib that can be pipped.
cntk.tests.test_utils.set_device_from_pytest_env() # (only needed for our build system)
C.cntk_py.set_fixed_random_seed(1) # fix the random so that LR exmaples are repeatable.

# Define the network
input_dim = 2
num_output_classes = 2

# Ensure that we always get the same results
np.random.seed(0)

# 1------Data------
# Helper function to generate a random data sample
def generate_random_data_sample(sample_size, feature_dim, num_classes):
	# Create synthetic data using Numpy.
	Y = np.random.randint(size=(sample_size,1), low=0, high=num_classes)
	
	# Make sure that the data is separable
	X = (np.random.randn(sample_size, feature_dim)+3) * (Y+1)

	# Specify the data type to match the input variable used later in the tutorial
	# (default type is double)
	X = X.astype(np.float32)

	# convert class 0 into the vector "1 0 0"
	# class 1 into the vector "0 1 0", ...
	class_ind = [Y==class_number for class_number in range(num_classes)]
	Y = np.asarray(np.hstack(class_ind), dtype=np.float32)
	return X,Y

mysamplesize = 32
features, labels = generate_random_data_sample(mysamplesize, input_dim, num_output_classes)
print (features, labels)

# Plot the data
import matplotlib.pyplot as plt
#%matplotlib inline #errors:SyntaxError: invalid syntax

# Let 0 represent malignant/red and 1 represent benign/blue
colors = ['r' if label == 0 else 'b' for label in labels[:,0]] # all lows for 0th comlumn

plt.scatter(features[:,0], features[:,1], c=colors)
plt.xlabel("Age (scaled)")
plt.ylabel("Tumor size (in cm)")
plt.show()

# 2------Model Creation------
feature = C.input_variable(input_dim, np.float32)
print (feature)

# network setup
# Define a dictionary to store the model parameters
mydict = {}

def linear_layer(input_var, output_dim):
	input_dim = input_var.shape[0]
	weight_param = C.parameter(shape=(input_dim, output_dim))
	bias_param = C.parameter(shape=(output_dim))

	mydict['w'], mydict['b'] = weight_param, bias_param

	return C.times(input_var, weight_param) + bias_param

# 3------Training------

output_dim = num_output_classes
z = linear_layer(feature, output_dim)
label = C.input_variable(num_output_classes, np.float32)
loss = C.cross_entropy_with_softmax(z, label)

print(z)

# Evaluation
eval_error= C.classification_error(z, label)

# Optimizer
# Instantiate the trainer object to drive the model training
learning_rate = 0.5
lr_schedule = C.learning_rate_schedule(learning_rate, C.UnitType.minibatch)
learner = C.sgd(z.parameters, lr_schedule)
trainer = C.Trainer(z, (loss, eval_error), [learner])

# Define a utility function to compute the moving average.
# A more efficient implementation is possible with np.cumsum() function
# 2018-02-07
def moving_average(a, w=10):
	if len(a) < w:
		return a[:]
	return [val if idx < w else sum(a[(idx-w):idx])/w for idx, val in enumerate(a)]

# Define a utility that prints the training progress
def print_training_progress(trainer, mb, frequency, verbose=1):
	training_loss, eval_error = "NA", "NA"

	if mb % frequency == 0:
		training_loss = trainer.previous_minibatch_loss_average
		eval_error = trainer.previous_minibatch_evaluation_average
		if verbose:
			print ("Minibatch: {0}, Loss: {1:.4f}, Error: {2:.2f}".format(mb, training_loss, eval_error))

	return mb, training_loss, eval_error


#-------Run Training------
isTrain = False  # not to train and evaluate directly with model trained
modelFile = r'E:\ProgramLib\Python\CNTK\model\CNTK101-LR-CancerClassifier.cmf'
if not isTrain :
	# Load model
    z = C.Function.load(modelFile)
    print ("Loading model")
else:
    # Initialize the parameters for the trainer
    minibatch_size = 25
    num_samples_to_train = 10000
    num_minibatches_to_train = int(num_samples_to_train / minibatch_size)

    from collections import defaultdict

    # Run the trainer and perform model training
    training_progress_output_freq = 50
    plotdata = defaultdict(list)

    for i in range(0, num_minibatches_to_train):
        features, labels = generate_random_data_sample(minibatch_size, input_dim, num_output_classes)
        # Assign the minibatch data to the input variables and train the model on the minibatch
        trainer.train_minibatch({feature : features, label : labels})
        batchsize, loss, error = print_training_progress(trainer, i, training_progress_output_freq, verbose=1)

        if not (loss == "NA" or error == "NA"):
            plotdata["batchsize"].append(batchsize)
            plotdata["loss"].append(loss)
            plotdata["error"].append(error)

    """
Minibatch: 0, Loss: 0.6931, Error: 0.32
Minibatch: 50, Loss: 0.1884, Error: 0.08
Minibatch: 100, Loss: 0.4162, Error: 0.12
Minibatch: 150, Loss: 0.7879, Error: 0.40
Minibatch: 200, Loss: 0.1258, Error: 0.04
Minibatch: 250, Loss: 0.1313, Error: 0.08
Minibatch: 300, Loss: 0.1012, Error: 0.04
Minibatch: 350, Loss: 0.1068, Error: 0.04
Selected CPU as the process wide default device.
    """
# Compute the moving average loss to smooth out the noise in SGD
    plotdata["avgloss"] = moving_average(plotdata["loss"])
    plotdata["avgerror"] = moving_average(plotdata["error"])

# Plot the training loss and the training error
    import matplotlib.pyplot as plt

    plt.figure(1)
    plt.subplot(211)
    plt.plot(plotdata["batchsize"], plotdata["avgloss"], "b--")
    plt.xlabel('Minibatch number')
    plt.ylabel('Loss')
    plt.title('Minibatch run vs. Training loss')
    plt.show()

    plt.subplot(212)
    plt.plot(plotdata["batchsize"], plotdata["avgerror"], 'r--')
    plt.xlabel('Minibatch number')
    plt.ylabel('Label Prediction Error')
    plt.title('Minibatch run vs. Label Prediction Error')
    plt.show()

    # Save model


#------Evaluation/Testing------
#2018-02-08
# Run the trained model on a newly generated dataset
test_minibatch_size = 25
features, labels = generate_random_data_sample(test_minibatch_size, input_dim, num_output_classes)
trainer.test_minibatch({feature : features, label : labels})
print (features)
# prediction/evaluation
out = C.softmax(z)
if isTrain :
    result = out.eval({feature : features})
else:
    result = out.eval(features)
print ("Label     :", [np.argmax(label) for label in labels])
print ("Predicted :", [np.argmax(x) for x in result])
if isTrain:
    z.save(modelFile)
#------Visualization------
# Model parameters
print(mydict['b'].value)

bias_vector = mydict['b'].value
weight_matrix = mydict['w'].value

# Plot the data
import matplotlib.pyplot as plt

if isTrain :
# Let 0 represent malignant/red, and 1 represent benign/blue
    colors = ['r' if label == 0 else 'b' for label in labels[:,0]]
    plt.scatter(features[:,0], features[:,1], c=colors)    # draw dots
    plt.plot([0, bias_vector[0]/weight_matrix[0][1]],      # draw continuous curve
         [bias_vector[1]/weight_matrix[0][0], 0], c = 'g', lw = 3)
    plt.xlabel("Patient age (scaled)")
    plt.ylabel("Tumor size (in cm)")
    plt.show()
