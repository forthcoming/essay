function [stdata] = standardizeData(data)
%Standardize Data


X = data(:, 1);
Y = data(:, 2);
m = length(Y); % number of training examples
stdata = zeros(m, 2); % initialize fitting parameters

% StdDev = SQRT( sum[(X-mean)^2/(n-1)]  )
meanX = mean(X);
stdX = std(X);

for i = 1:m
    
    X(i) = ((X(i) - meanX)/stdX);
end

%Standardize(X) = X-mean /Std(X)

meanY = mean(Y);
stdY = std(Y);

for i = 1:m
    
    Y(i) = ((Y(i) - meanY)/stdY);   
end

 stdata(:, 1)= X(:);
 stdata(:, 2)=Y(:);










