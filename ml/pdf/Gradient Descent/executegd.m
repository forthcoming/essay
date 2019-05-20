clear ; close all; clc



%% ======================= Part 1: Load Data ==============================
% Load Data
fprintf('Plotting Data ...\n')
data = load('data.txt');

%% ======================= Part 2: Standardize Data =======================
% Standardize Data
data = standardizeData(data);
X = data(:, 1);
y = data(:, 2);
m = length(y); % number of training examples


%% ======================= Part 3: Plotting ===============================
% Plot Data
plotData(X, y);

fprintf('Program paused. Press enter to continue.\n');
pause;

%% =================== Part 4: Prediction Error - Copmute Cost ============
fprintf('Running Gradient Descent ...\n')

X = [ones(m, 1), data(:,1)]; % Add a column of ones to x
theta = zeros(2, 1); % initialize fitting parameters

% Some gradient descent settings
iterations = 1500;
alpha = 0.01;

% compute and display initial cost
predictionError(X, y, theta)

%% =================== Part 5: Gradient descent ===========================
% run gradient descent
theta = gradientDescent(X, y, theta, alpha, iterations);

% print theta to screen
fprintf('Theta found by gradient descent: ');
fprintf('%f %f \n', theta(1), theta(2));

% Plot the linear fit
hold on; % keep previous plot visible
plot(X(:,2), X*theta, '-')
legend('Training data', 'Linear regression')
hold off % don't overlay any more plots on this figure


