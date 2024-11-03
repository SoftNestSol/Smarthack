class Connection:
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
        self.distance = int(distance)
        self.lead_time_days = int(lead_time_days)
        self.connection_type = connection_type
        self.max_capacity = int(max_capacity)

    def get_movement_cost(self, amount):
        if self.connection_type == "pipeline":
            return self.distance * amount * self.pipeline_costPerDistanceAndVolume
        else:
            return self.distance * amount * self.truck_costPerDistanceAndVolume

    def get_movement_co2(self, amount):
        if self.connection_type == "pipeline":
            return self.distance * amount * self.pipeline_co2PerDistanceAndVolume
        else:
            return self.distance * amount * self.truck_co2PerDistanceAndVolume

    def get_overuse_penalty(self, amount):
        if self.connection_type == "pipeline":
            return amount * self.pipeline_overUsePenaltyPerVolume
        else:
            return amount * self.truck_overUsePenaltyPerVolume

    def move_from_to(self, amount, from_node, to_node):
        if to_node.name == "tank":
            to_node.initial_stock += amount
            from_node.decrease_stock(amount)
        else:
            to_node.fulfill(amount)
            from_node.decrease_stock(amount)


class Customer:
    def __init__(
        self,
        id,
        name,
        max_input,
        over_input_penalty,
        late_delivery_penalty,
        early_delivery_penalty,
        node_type,
    ):
        self.id = id
        self.name = name
        self.max_input = max_input
        self.over_input_penalty = over_input_penalty
        self.late_delivery_penalty = late_delivery_penalty
        self.early_delivery_penalty = early_delivery_penalty
        self.node_type = node_type


class Demand:
    def __init__(self, customerId, amount, postDay, startDay, endDay):
        self.customer_id = customerId
        self.amount = amount
        self.total_amount = amount
        self.post_day = postDay
        self.start_day = startDay
        self.end_day = endDay
        self.cost = 0
        self.co2 = 0

    def __lt__(self, other):
        return self.start_day < other.start_day or self.cost < other.cost or self.co2 < other.co2

    def partially_fullfill(self, amount):
        self.amount -= amount


class Refinery:
    def __init__(
        self,
        id,
        name,
        capacity,
        max_output,
        production,
        overflow_penalty,
        underflow_penalty,
        over_output_penalty,
        production_cost,
        production_co2,
        initial_stock,
        node_type,
    ):
        self.id = id
        self.name = name
        self.capacity = int(capacity)
        self.max_output = int(max_output)
        self.production = int(production)
        self.overflow_penalty = overflow_penalty
        self.underflow_penalty = float(underflow_penalty)
        self.over_output_penalty = over_output_penalty
        self.production_cost = float(production_cost)
        self.production_co2 = float(production_co2)
        self.initial_stock = int(initial_stock)
        self.node_type = node_type
        self.generated_co2 = 0
        self.generated_cost = 0
        self.connected_to = []

    def refinery_produce(self):
        self.initial_stock += self.production
        self.generated_co2 += self.production_co2
        self.generated_cost += self.production_cost

    def decrease_stock(self, amount):
        self.initial_stock -= amount

    def get_connections(self):
        return self.connected_to


class Tank:
    def __init__(
        self,
        id,
        name,
        capacity,
        max_input,
        max_output,
        overflow_penalty,
        underflow_penalty,
        over_input_penalty,
        over_output_penalty,
        initial_stock,
        node_type,
    ):
        self.id = id
        self.name = name
        self.capacity = int(capacity)
        self.max_input = max_input
        self.max_output = max_output
        self.overflow_penalty = overflow_penalty
        self.underflow_penalty = underflow_penalty
        self.over_input_penalty = over_input_penalty
        self.over_output_penalty = over_output_penalty
        self.initial_stock = int(initial_stock)
        self.node_type = node_type
        self.connected_to = []
