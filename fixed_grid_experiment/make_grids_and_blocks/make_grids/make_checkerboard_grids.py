import numpy as np
import random
from gerrychain import Graph
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.colors import ListedColormap, BoundaryNorm
import networkx as nx
import os

SCRIPT_FILE_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_FILE_PATH)

# Modify these variables to change random seed, size of NxN grid, number of red units, number of grids you want made
random_seed = 100
N = 12
num_r_units = 72
number_grids_to_make = 5

NUM_NODES = N * N
num_blue = NUM_NODES - num_r_units

random.seed(random_seed)
np.random.seed(random_seed)

def main():
    """Creates number_grids_to_make NxN grid graphs with low assortativity. Each unit in the grid has population 1
    and represents either one blue or one red vote.

    Grids are saved as .json files. Images are saved as .png files.
    """
    for map_number in range(1, number_grids_to_make + 1):
        create_low_assortativity_grid(map_number)
        save_grid_image(map_number)

def create_low_assortativity_grid(map_number):

    # Create NxN grid and assign random red/blue values to each node
    graph = Graph.from_networkx(nx.grid_2d_graph(N,N))
    graph = Graph.from_networkx(nx.relabel.convert_node_labels_to_integers(graph, label_attribute ="old_node_index"))

    units = list(graph.nodes)
    random.shuffle(units)
    unit_partisan_assignments = {}
    b_counter = 0
    r_counter = 0
    for unit in units:
        if r_counter != num_r_units:
            unit_partisan_assignments[unit] = 0
            r_counter = r_counter + 1
        else:
            unit_partisan_assignments[unit] = 1
            b_counter = b_counter + 1

    # Check the right number of units were assigned D/R.
    assert(r_counter == num_r_units), "Something went terribly wrong. Map did not assign correct number of red units."
    assert(b_counter == NUM_NODES-num_r_units), "Something went terribly wrong. Map did not assign correct number of blue units."

    # Save population, voter data to graph.
    for unit, data in graph.nodes(data=True):
        data['population'] = 1
        if unit_partisan_assignments[unit] == 1:
            data['B'] = 1
            data['R'] = 0 
        else:    
            data['B'] = 0
            data['R'] = 1

    def cut_edges(graph):
        """Count number of cut edges of the current grid."""
        count = 0

        for u, v in graph.edges():
            if graph.nodes[u]["R"] != graph.nodes[v]["R"]:
                count += 1

        return count

    def swap_score_change(graph, i, j):
        """
        Compute the change in the number of cut edges that would result
        from swapping the blue/red assignments of nodes i and j.
        """

        if graph.nodes[i]["R"] == graph.nodes[j]["R"]:
            return 0

        score_change = 0

        # Compute the number of cut edges of each of the nodes
        # involved in the swap.
        for u in (i, j):
            for v in graph.neighbors(u):

                # Skip the edge between i and j, since it will always be cut
                if v == i or v == j:
                    continue

                # True if the edge between u and v was cut before the swap, else False
                before = (
                    graph.nodes[u]["R"] != graph.nodes[v]["R"]
                )

                # True if the edge between u and v is cut after the swap, else False
                after = (
                    (1 - graph.nodes[u]["R"]) != graph.nodes[v]["R"]
                )

                # Score change is either +1 or -1
                score_change += int(after) - int(before)

        return score_change

    score = cut_edges(graph)

    for step in range(20000):

        reds = [
            u for u in graph.nodes()
            if graph.nodes[u]["R"] == 1
        ]

        blues = [
            v for v in graph.nodes()
            if graph.nodes[v]["B"] == 1
        ]

        # Randomly select red node, blue node
        i = random.choice(reds)
        j = random.choice(blues)

        # Change the total number of cut edges in the grid by the potential change of the swap
        d = swap_score_change(graph, i, j)
        new_score = score + d

        # If the new score is better, accept the swap; if not, accept the swap only
        # with a small probability
        if new_score > score:
            accept = True
        else:
            accept = random.random() < 0.01

        if accept:
            # Swap the blue/red assigments of the nodes
            graph.nodes[i]["R"], graph.nodes[j]["R"] = (
                graph.nodes[j]["R"],
                graph.nodes[i]["R"]
            )

            graph.nodes[i]["B"], graph.nodes[j]["B"] = (
                graph.nodes[j]["B"],
                graph.nodes[i]["B"]
            )

            score = new_score

        if step % 2000 == 0:
            print(step, score)

    print("\nFinal cut edges:", score)

    save_grid_maps_to = (
        f"{SCRIPT_DIR}/grids/map_.jsons/low_assortativity_grid_{map_number}.json"
    )
    os.makedirs(os.path.dirname(save_grid_maps_to), exist_ok=True)
    graph.to_json(save_grid_maps_to)

def save_grid_image(map_number):
    graph = Graph.from_json(f"{SCRIPT_DIR}/grids/map_.jsons/low_assortativity_grid_{map_number}.json")

    # Create a 2D array in which each subarray is one row of the grid graph
    # Each subarray is N entries of either 1 (blue vote) or 0 (red vote)
    grid_2D_array = []
    count = 0
    grid_row_array = []
    for unit, data in graph.nodes(data=True):
        if count != N:
            grid_row_array.append(int(data['B']))
            count = count + 1
            if count == N:
                grid_2D_array.append(grid_row_array)  
        else:
            count = 0
            grid_row_array = []
            grid_row_array.append(int(data['B']))
            count = 1
        
    # Use 2D array to create image of grid map
    grid_data = grid_2D_array
    cmap = matplotlib.colors.ListedColormap(['#E62020', '#1560BD'])
    bounds = [0,1]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    fig, ax = plt.subplots()
    ax.imshow(grid_data, cmap=cmap, norm=norm)
    ax.grid(which='major', axis='both', linestyle='-', color='k', linewidth=2)
    ax.set_xticks(np.arange(-0.5, N, 1))
    ax.set_yticks(np.arange(-0.5, N, 1))
    ax.set_yticklabels([])
    ax.set_xticklabels([])

    save_grid_map_images_to = (
        f"{SCRIPT_DIR}/grids/map_.pngs/low_assortativity_grid_{map_number}.png"
    )
    os.makedirs(os.path.dirname(save_grid_map_images_to), exist_ok=True)
    plt.savefig(save_grid_map_images_to)

main()
