function p = mypredict(Weight_1, Weight_2, input_node)

%Forward Propagation
input_sigma = input_node*Weight_1;
hidden_node = sigmoid(input_sigma); % 1*3
hidden_sigma = hidden_node*Weight_2';
output_node = sigmoid(hidden_sigma);


for jj=1:1000
    %sigmoid' = f(x)(1-f(x))
    %output_node_prime = s'(inner_sigma)*margin
    if jj>1
        Weight_2 = Weight_2_prime;
        Weight_1 = Weight_1_prime;
    end 
        margin = 0 - output_node;
        sigmoid_prime_hidden_sigma = sigmoid(hidden_sigma);
        output_node_prime = (sigmoid_prime_hidden_sigma *(1-sigmoid_prime_hidden_sigma))*margin;
        
        delta_weight = (output_node_prime)./hidden_node; % 1*3
        Weight_2_prime = Weight_2 + delta_weight; 
                
        sigmoid__prime_input_sigma = sigmoid_derivative(input_sigma);
        mydivide = output_node_prime./Weight_2;
        hidden_node_prime = zeros(1,3);
        hidden_node_prime(1,1) = mydivide(1,1) * sigmoid__prime_input_sigma(1,1);
        hidden_node_prime(1,2) = mydivide(1,2) * sigmoid__prime_input_sigma(1,2);
        hidden_node_prime(1,3) = mydivide(1,3) * sigmoid__prime_input_sigma(1,3);  
   
        delta_weight_2 = hidden_node_prime'*input_node;

        Weight_1_prime = Weight_1 + delta_weight_2';

        input_sigma = input_node*Weight_1_prime;
        hidden_node = sigmoid(input_sigma); % 1*3
        hidden_sigma = hidden_node*Weight_2_prime';
        output_node = sigmoid(hidden_sigma);
end

p = output_node;

end