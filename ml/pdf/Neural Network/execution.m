%% Machine Learning -  Neural Networks  - Simple Example

%% Initialization
clear ; close all; clc

input_node = [1 1]; %1*2

% Generate Weight By Gausian Distribution
Weight_1 = [ -0.5 1.01  0.23 ; -0.32 -0.24 -0.12 ]; %2*3
Weight_2 = [ 0.15 1.32 -0.37 ]; %1*3
pred = mypredict(Weight_1, Weight_2, input_node);

