function [theta] = gradientDescent(X, y, theta, alpha, num_iters)
%GRADIENTDESCENT Performs gradient descent to learn theta
%   theta = GRADIENTDESENT(X, y, theta, alpha, num_iters) updates theta by 
%   taking num_iters gradient steps with learning rate alpha

% Initialize some useful values
%m = length(y); % number of training examples
J_history = zeros(num_iters, 1);

m = length(y); % number of training examples

for iter = 1:num_iters

    if iter == 1
        J_history(iter) = predictionError(X, y, theta);
 
    elseif iter > 1
        A=X(:,2);
        B=-(y-(X*theta));
        C=B'*A;


        DefSSEb = sum(B);
        DefSSEa = sum(C);

        bold=theta(1,1);
        aold=theta(2,1);

        theta(1,1) = (bold - (alpha*(DefSSEb/m)));
        theta(2,1) = (aold - (alpha*(DefSSEa/m)));

        J_history(iter) = predictionError(X, y, theta);
   end
 
end

theta = theta(:);
end
