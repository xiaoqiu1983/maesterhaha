import tensorflow.compat.v1 as tf
import numpy as np
import os
import argparse
import tflearn
FEATURE_NUM =128
ACTION_EPS = 1e-4
GAMMA = 0.99
def add_batch_dimension(data,batch=1):
    shape=data.shape
    dim=len(shape)
    if dim==1:
        width=int(len(data)/batch)
        return np.asarray(data[:]).reshape((batch,width))
    elif dim==2:
        height=int(shape[0]/batch)
        width=shape[1]
        return np.asarray(data[:]).reshape((batch,height,width))
    else:
        raise Exception("dimision error")
def print_net_info(sess,trainable_var,log_v=False):
    for param in trainable_var:
        print(param.name)
        if log_v:
            result=sess.run(param)
            print(result)
            #print(param.numpy())
class Network():
    def __init__(self,state_dim, action_dim, learning_rate,scope='actor'):
        self._entropy = 0.5
        self.s_dim=state_dim
        self.a_dim=action_dim
        self.lr_rate = learning_rate
        self.R = tf.placeholder(tf.float32, [None, 1])
        self.inputs = tf.placeholder(tf.float32, [None, self.s_dim[0], self.s_dim[1]])
        self.old_pi = tf.placeholder(tf.float32, [None, self.a_dim])
        self.acts = tf.placeholder(tf.float32, [None, self.a_dim])
        self.entropy_weight = tf.placeholder(tf.float32)
        self.pi, self.val = self.create_network(inputs=self.inputs,scope=scope)
        self.real_out = tf.clip_by_value(self.pi, ACTION_EPS, 1. - ACTION_EPS)
        self.log_prob = tf.log(tf.reduce_sum(tf.multiply(self.real_out, self.acts), reduction_indices=1, keepdims=True))
        self.entropy = tf.multiply(self.real_out, tf.log(self.real_out))
        self.adv = tf.stop_gradient(self.R - self.val)
        self.a2closs = self.log_prob * self.adv
        # Get all network parameters
        self.network_params = \
            tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES,scope=scope)

        # Set all network parameters
        self.input_network_params = []
        for param in self.network_params:
            self.input_network_params.append(
                tf.placeholder(tf.float32, shape=param.get_shape()))
        self.set_network_params_op = []
        for idx, param in enumerate(self.input_network_params):
            self.set_network_params_op.append(
                self.network_params[idx].assign(param))
        
        self.loss = - tf.reduce_sum(self.a2closs) \
            + self.entropy_weight * tf.reduce_sum(self.entropy)
        
        self.optimize = tf.train.AdamOptimizer(self.lr_rate).minimize(self.loss)
        self.val_loss = tflearn.mean_square(self.val, self.R)
        self.val_opt = tf.train.AdamOptimizer(self.lr_rate * 10.).minimize(self.val_loss)
    def create_network(self,inputs,scope):
        with tf.variable_scope(scope):
            split_0 = tflearn.fully_connected(
                inputs[:, 0:1, -1], FEATURE_NUM, activation='relu')
            split_1 = tflearn.fully_connected(
                inputs[:, 1:2, -1], FEATURE_NUM, activation='relu')
            split_2 = tflearn.conv_1d(
                inputs[:, 2:3, :], FEATURE_NUM, 1, activation='relu')
            split_3 = tflearn.conv_1d(
                inputs[:, 3:4, :], FEATURE_NUM, 1, activation='relu')
            split_4 = tflearn.conv_1d(
                inputs[:, 4:5, :self.a_dim], FEATURE_NUM,1, activation='relu')
            split_5 = tflearn.fully_connected(
                inputs[:, 5:6, -1], FEATURE_NUM, activation='relu')
            split_2_flat = tflearn.flatten(split_2)
            split_3_flat = tflearn.flatten(split_3)
            split_4_flat = tflearn.flatten(split_4)

            merge_net = tflearn.merge(
                [split_0, split_1, split_2_flat, split_3_flat, split_4_flat,split_5], 'concat')

            pi_net = tflearn.fully_connected(
                merge_net,FEATURE_NUM, activation='relu')
            v_net = tflearn.fully_connected(
                merge_net, FEATURE_NUM, activation='relu')            
            pi = tflearn.fully_connected(pi_net, self.a_dim, activation='softmax')
            v=tflearn.fully_connected(v_net, 1, activation='linear')
            return pi,v
    def predict(self, sess,input):
        action=sess.run(self.real_out,feed_dict={self.inputs:input})
        return action[0]
    def print_net_info(self,sess):
        print_net_info(sess,self.network_params,True)
    def get_network_params(self,sess):
        return sess.run(self.network_params)
    def set_network_params(self, sess,input_network_params):
        sess.run(self.set_network_params_op, feed_dict={
            i: d for i, d in zip(self.input_network_params, input_network_params)
        })
    def r(self, pi_new, pi_old, acts):
        return tf.reduce_sum(tf.multiply(pi_new, acts), reduction_indices=1, keepdims=True) / \
                tf.reduce_sum(tf.multiply(pi_old, acts), reduction_indices=1, keepdims=True)
    def set_entropy_decay(self, decay=0.6):
        self._entropy *= decay
    def get_entropy(self):
        return np.clip(self._entropy, 0.001, 0.5)
    def train(self,sess,s_batch, a_batch, p_batch, v_batch, epoch):
        s_batch, a_batch, p_batch, v_batch = tflearn.data_utils.shuffle(s_batch, a_batch, p_batch, v_batch)
        sess.run([self.optimize, self.val_opt], feed_dict={
            self.inputs: s_batch,
            self.acts: a_batch,
            self.R: v_batch, 
            self.old_pi: p_batch,
            self.entropy_weight:self.get_entropy()
        })
    def compute_v(self, sess,s_batch, a_batch, r_batch, terminal):
        ba_size = len(s_batch)
        R_batch = np.zeros([len(r_batch), 1])

        if terminal:
            R_batch[-1, 0] = 0  # terminal state
        else:    
            v_batch =sess.run(self.val, feed_dict={
                self.inputs: s_batch
            })
            R_batch[-1, 0] = v_batch[-1, 0]  # boot strap from last state
        for t in reversed(range(ba_size - 1)):
            R_batch[t, 0] = r_batch[t] + GAMMA * R_batch[t + 1, 0]

        return list(R_batch)
