class rafinery:
    def __init__(self,id, name, capacity, max_output, production, overflow_penalty, underflow_penalty, over_output_penalty, production_cost, production_co2, initial_stock, node_type):
        self.id = id
        self.name = name
        self.capacity = capacity
        self.max_output = max_output
        self.production = production
        self.overflow_penalty = overflow_penalty
        self.underflow_penalty = underflow_penalty
        self.over_output_penalty = over_output_penalty
        self.production_cost = production_cost
        self.production_co2 = production_co2
        self.initial_stock = initial_stock
        self.node_type = node_type
        self.generated_co2 = 0
        self.generated_cost = 0

    
    def refinery_produce(self):
        self.initial_stock += self.production
        self.generated_co2 += self.production_co2
        self.generated_cost += self.production_cost


    def decrease_stock(self, amount):
        self.initial_stock -= amount




class tank:
    def __init__(self, id, name, capacity, max_input, max_output, overflow_penalty, underflow_penalty, over_input_penalty, over_output_penalty, initial_stock, node_type):
        self.id = id
        self.name = name
        self.capacity = capacity
        self.max_input = max_input
        self.max_output = max_output
        self.overflow_penalty = overflow_penalty
        self.underflow_penalty = underflow_penalty
        self.over_input_penalty = over_input_penalty
        self.over_output_penalty = over_output_penalty
        self.initial_stock = initial_stock
        self.node_type = node_type


class connection:

    pipeline_costPerDistanceAndVolume = 0.05
    pipeline_co2PerDistanceAndVolume = 0.02
    pipeline_overUsePenaltyPerVolume = 1.13

    truck_costPerDistanceAndVolume = 0.42
    truck_co2PerDistanceAndVolume = 0.31
    truck_overUsePenaltyPerVolume = 0.73

    def __init__(self, id, from_id, to_id, distance, lead_time_days, connection_type, max_capacity):
        self.id = id
        self.from_id = from_id
        self.to_id = to_id
        self.distance = distance
        self.lead_time_days = lead_time_days
        self.connection_type = connection_type
        self.max_capacity = max_capacity

    
    def get_movement_cost(self, amount):
        if self.connection_type == "pipeline":
            return self.distance*amount* self.pipeline_costPerDistanceAndVolume
        else:
            return self.distance*amount* self.truck_costPerDistanceAndVolume
    
    def get_movement_co2(self, amount):
        if self.connection_type == "pipeline":
            return self.distance*amount* self.pipeline_co2PerDistanceAndVolume
        else:
            return self.distance*amount* self.truck_co2PerDistanceAndVolumes
    
    def get_overuse_penalty(self, amount):
        if self.connection_type == "pipeline":
            return amount* self.pipeline_overUsePenaltyPerVolume
        else:
            return amount* self.truck_overUsePenaltyPerVolume
        
    def move_from_to(self, amount, from_node, to_node):
        from_node.decrease_stock(amount)
        to_node.initial_stock += amount
        
        if to_node.name == "customer":
            to_node.fulfill(amount)
            



class customers:
    def __init__(self, id, name, max_input, over_input_penalty, late_delivery_penalty, early_delivery_penalty, node_type):
        self.id = id
        self.name = name
        self.max_input = max_input
        self.over_input_penalty = over_input_penalty
        self.late_delivery_penalty = late_delivery_penalty
        self.early_delivery_penalty = early_delivery_penalty
        self.node_type = node_type
        self.orders = []


    def fulfill(self, amount):
        for order in self.orders:
            if order.amount > amount:
                order.amount -= amount
                break
            else:
                amount -= order.amount
                self.orders.remove(order)



