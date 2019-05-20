function y = sigmoid_derivative(x)

 %sigmoid' = f(x)*(1-f(x))

 sigmoid_helper_2 = zeros(1,3);
    for i=1:3
        a= x(1,i);
        sigmoid_helper_2(1,i)= sigmoid(a)*(1-sigmoid(a));
    end
 y = sigmoid_helper_2;
        
end 
 