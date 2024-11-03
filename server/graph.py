import heapq


def get_shortest_path_for_customer(graph, start_id):
    pq = []
    heapq.heappush(pq, (0, start_id))

    shortest_times = {start_id: 0}

    while pq:
        current_time, current_id = heapq.heappop(pq)

        if int(current_time) > int(shortest_times[current_id]):
            continue

        for neighbor_id, time_cost in graph.get(current_id, []):
            new_time = int(current_time) + int(time_cost)

            if neighbor_id not in shortest_times or new_time < int(shortest_times[neighbor_id]):
                shortest_times[neighbor_id] = new_time
                heapq.heappush(pq, (new_time, neighbor_id))

    ordered_nodes = sorted(shortest_times.items(), key=lambda x: x[1])
    return ordered_nodes
