import networkx as nx
import numpy as np
import random
import os
from gerrychain import Graph
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.colors import ListedColormap, BoundaryNorm
from scipy.ndimage import gaussian_filter

SCRIPT_FILE_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_FILE_PATH)

N = 12
NUM_NODES = N * N
random_seed = 452
random.seed(random_seed)

def main():
    """Creates grid graphs that will be used in synthetic experiments.

    Each of these is a 12x12 grid where each unit has population 1
    and represents either one Democratic or one Republic vote.

    Creates nine maps total:
    three of these have 58 Republicans and 86 Democrats (approx. a 40% R–60% D split),
    three of these have 72 Republicans and 72 Democrats (a 50%-50% split),
    and three of these have 86 Republicans and 58 Democrats (approx. a 60% R–40% D split).

    Also creates .png images of these maps.
    """

    for num_r_units in [72, 58, 86]:
        for map_number in [1, 2, 3]:
            create_clustered_dual_graph(num_r_units, map_number)
            create_dual_graph_image(num_r_units, map_number)

def create_clustered_dual_graph(num_r_units, map_number):
    """Creates .json files for maps described above.

    Args:
        num_r_units: number of red votes (out of N^2 total)
        map_number: number that will go into grid title for organizational purposes
    """
    save_grid_maps_to = (
        f"{SCRIPT_DIR}/grids/map_.jsons/"
        f"high_assortativity_map_{map_number}.json"
    )
    os.makedirs(os.path.dirname(save_grid_maps_to), exist_ok=True)
    
    # Create blank NxN grid
    unit_dual_graph = Graph.from_networkx(nx.grid_2d_graph(N,N))
    unit_dual_graph = Graph.from_networkx(nx.relabel.convert_node_labels_to_integers(unit_dual_graph, label_attribute ="old_node_index"))

    # Assign each unit a random value between 0 and 1, then smooth
    noise = np.random.rand(N, N)
    smooth = gaussian_filter(noise, sigma=1.6) 

    # Choose exactly num_r_units highest as R
    flat = smooth.flatten()
    cut = np.partition(flat, -num_r_units)[-num_r_units]

    grid_assign = (smooth >= cut).astype(int)  # 1 = R, 0 = B

    # Build assignment dict keyed by node id
    unit_partisan_assignments = {}

    for node, data in unit_dual_graph.nodes(data=True):
        i, j = data["old_node_index"]   # original grid coordinate
        unit_partisan_assignments[node] = int(grid_assign[i, j])

    # Sanity checks
    r_counter = sum(unit_partisan_assignments.values())
    b_counter = NUM_NODES - r_counter
    assert r_counter == num_r_units, "Something went terribly wrong. Map did not assign correct number of red units."
    assert b_counter == NUM_NODES - num_r_units, "Something went terribly wrong. Map did not assign correct number of blue units."

    # Attach attributes to graph
    for unit, data in unit_dual_graph.nodes(data=True):
        data['population'] = 1
        if unit_partisan_assignments[unit] == 1:
            data['B'] = 0
            data['R'] = 1
        else:
            data['B'] = 1
            data['R'] = 0

    unit_dual_graph.to_json(save_grid_maps_to)


def create_dual_graph_image(num_r_units, map_number):
    """Creates .png images for the grids described above.

    Args:
        num_r_units: number of red votes (out of N^2 total)
        map_number: number that will go into grid title for organizational purposes
    """
    save_grid_map_images_to = (
        f"{SCRIPT_DIR}/grids/map_.pngs/"
        f"high_assortativity_map_{map_number}.png"
    )
    os.makedirs(os.path.dirname(save_grid_map_images_to), exist_ok=True)

    # Access appropriate dual graph .json file
    unit_dual_graph_json = (
        f"{SCRIPT_DIR}/grids/map_.jsons/"
        f"high_assortativity_map_{map_number}.json"
    )

    unit_dual_graph = Graph.from_json(unit_dual_graph_json)
    
    # Create a 2D array in which each subarray is one row of the grid graph
    # Each subarray is N entries of either 1 (Dem vote) or 0 (Rep vote)
    grid_2D_array = []
    count = 0
    grid_row_array = []
    for unit, data in unit_dual_graph.nodes(data=True):
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

    plt.savefig(save_grid_map_images_to)

main()
