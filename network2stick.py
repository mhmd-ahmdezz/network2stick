import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import itertools

def generate_full_node_path(edges, gate_sequence):
    """
    Takes a list of transistor edges and an Euler gate sequence.
    Returns the sequence of nodes that satisfies the gate sequence.
    """
    G = nx.MultiGraph()
    for u, v, label in edges:
        G.add_edge(u, v, key=label, transistor=label)

    # We determine the starting node by checking the first gate in the sequence
    first_gate = gate_sequence[0]
    possible_starts = []
    for u, v, k in G.edges(keys=True):
        if k == first_gate:
            possible_starts.extend([u, v])

    # Test each potential starting node to see if it completes the chain
    for start_node in set(possible_starts):
        node_path = [start_node]
        current_node = start_node
        temp_edges = list(G.edges(keys=True))
        valid_chain = True

        for gate in gate_sequence:
            found_edge = False
            for i, (u, v, k) in enumerate(temp_edges):
                if k == gate:
                    if u == current_node:
                        current_node = v
                        found_edge = True
                    elif v == current_node:
                        current_node = u
                        found_edge = True
                    
                    if found_edge:
                        node_path.append(current_node)
                        temp_edges.pop(i)
                        break
            if not found_edge:
                valid_chain = False
                break
        
        if valid_chain:
            return node_path
    return None

def format_closed_path(nodes, gates):
    """Formats the path as Node - Gate - Node - Gate..."""
    path = []
    for i in range(len(gates)):
        path.append(str(nodes[i]))
        path.append(str(gates[i]))
    path.append(str(nodes[-1]))
    return " - ".join(path)
def find_best_euler_path(edges):
    """Finds a valid Euler path and returns both the gate sequence and the node sequence."""
    G = nx.MultiGraph()
    for u, v, label in edges:
        G.add_edge(u, v, key=label, transistor=label)
    valid_paths = []

    #Test every single permutation of our 4 transistors
    for perm in itertools.permutations(edges):
        
        # An Euler path can start at either endpoint of the first transistor
        first_edge = perm[0]
        
        for start_node in [first_edge[0], first_edge[1]]:
            is_valid = True
            current_node = start_node
            
            # 4. Attempt to walk through the edges in this permutation
            for edge in perm:
                u, v, k = edge
                
                # Check if the transistor connects to our current position
                if current_node == u:
                    current_node = v  # Move to the other side of the transistor
                elif current_node == v:
                    current_node = u  # Move to the other side of the transistor
                else:
                    is_valid = False  # The path is broken; diffusion break required
                    break
                    
            # If it's valid, store the sequence of gate labels
            if is_valid:
                gate_sequence = [edge[2] for edge in perm]
                
                # Avoid duplicate sequences in our output
                if gate_sequence not in valid_paths:
                    valid_paths.append(gate_sequence)
            #Print all valid permutations
    print(f"Found {len(valid_paths)} unique Euler paths:\n")
    for idx, path in enumerate(valid_paths, 1):
        print(f"Path {idx}: {' - '.join(path)}")
    return valid_paths

def draw_network(edges, title="Transistor Network Graph"):
    # 1. Initialize a clean MultiGraph
    # Starting empty prevents double-counting if you call add_edge later.
    G = nx.MultiGraph()
    for u, v, label in edges:
        G.add_edge(u, v, key=label, transistor=label)

    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(8, 6))

    # 2. Draw Nodes
    nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=1000)
    nx.draw_networkx_labels(G, pos, font_weight='bold')

    # 3. Draw Edges with Curvature
    # Standard draw_networkx_edges draws straight lines. 
    # For a MultiGraph, we loop through edges and apply a 'rad' curvature to parallel ones.
    ax = plt.gca()
    for u, v, k, data in G.edges(data=True, keys=True):
        all_variants = G.get_edge_data(u, v)
        if len(all_variants) > 1:
            # If multiple edges exist, assign different curvatures based on index
            keys = list(all_variants.keys())
            idx = keys.index(k)
            rad = 0.2 * (((idx % 2) * 2 - 1) * ((idx // 2) + 1))
        else:
            rad = 0.0
            
        nx.draw_networkx_edges(
            G, pos, 
            edgelist=[(u, v)], 
            connectionstyle=f'arc3, rad={rad}', 
            edge_color='gray', 
            width=2
        )

    # 4. Correctly Aggregate Edge Labels
    # Use a dictionary that combines all gate names for a node pair into one string.
    edge_labels_grouped = {}
    for u, v, k in G.edges(keys=True):
        # We sort (u, v) so the pair is consistent regardless of direction
        pair = tuple(sorted((u, v)))
        if pair not in edge_labels_grouped:
            # Fetch all gate labels between these two nodes
            all_gates = G.get_edge_data(u, v).keys()
            edge_labels_grouped[pair] = ", ".join(all_gates)

    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels_grouped, font_size=12)

    plt.title(title)
    plt.axis('off')
    plt.show()

def find_consistent_path(valid_paths_pun,valid_paths_pdn):
    consistent_path = []
    for i in valid_paths_pun:
        for j in valid_paths_pdn:
            if(i == j):
                consistent_path = i
                break
    
    if(len(consistent_path) != 0):
        print(f"Consistent Path is found : {consistent_path}")
    else :
        print("No Consistent Path is found")
    return consistent_path

def plot_stick_diagram(consistent_path, pun_nodes, pdn_nodes, output_node='F'):
    """
    Plots a professional CMOS stick diagram with connections.
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Grid and Layout Configuration - SCALED DOWN to avoid legend overlap
    num_gates = len(consistent_path)
    x_coords = np.arange(num_gates + 1) * 1.5   # Reduced from 2 to 1.5
    gate_x = x_coords[:-1] + 0.75               # Reduced from 1 to 0.75
    
    # Reduced vertical spacing
    y_vdd, y_pun, y_pdn, y_gnd, y_out = 8.5, 6.2, 2.8, 0.5, 4.5
    
    # Define colors
    c_pdiff = '#8B4513'      # p-diffusion brown
    c_ndiff = '#228B22'      # n-diffusion green
    c_poly = '#CC0000'       # polysilicon red
    c_rail = '#000000'       # power rail black
    c_metal_out = '#008B8B'  # output metal dark cyan
    c_metal_int = '#2F4F4F'  # intermediate metal dark slate gray
    c_contact = '#000000'    # contact black
    
    # 1. Draw Power Rails (Metal 1 - Blue/Black)
    ax.axhline(y=y_vdd, color='blue', linewidth=5)
    ax.text(-1.2, y_vdd + 0.25, 'VDD', color='blue', fontweight='bold', va='bottom', ha='right', fontsize=11)
    ax.axhline(y=y_gnd, color='black', linewidth=5)
    ax.text(-1.2, y_gnd + 0.25, 'GND', color='black', fontweight='bold', va='bottom', ha='right', fontsize=11)
    
    # 2. Draw Diffusion Strips (P-Diffusion: Brown, N-Diffusion: Green)
    ax.plot([x_coords[0]-0.4, x_coords[-1]+0.4], [y_pun, y_pun], color=c_pdiff, linewidth=12, alpha=0.6)
    ax.text(-1.2, y_pun, 'P-Diff', color=c_pdiff, fontweight='bold', va='center', ha='right', fontsize=10)
    ax.plot([x_coords[0]-0.4, x_coords[-1]+0.4], [y_pdn, y_pdn], color=c_ndiff, linewidth=12, alpha=0.6)
    ax.text(-1.2, y_pdn, 'N-Diff', color=c_ndiff, fontweight='bold', va='center', ha='right', fontsize=10)
    
    # 3. Draw Shared Polysilicon Gates (Red)
    for i, gate in enumerate(consistent_path):
        gx = gate_x[i]
        ax.plot([gx, gx], [y_pdn - 0.8, y_pun + 0.8], color=c_poly, linewidth=3, zorder=3)
        ax.text(gx, y_pun + 1.2, gate, color=c_poly, fontweight='bold', ha='center', fontsize=11)

    # 4. Map Node Positions for Wiring
    node_positions = {}

    def needs_contact(node, layer_nodes):
        if node in ['VDD', 'GND', output_node]:
            return True
        return layer_nodes.count(node) > 1

    # PDN (NMOS) Logic
    for i, node in enumerate(pdn_nodes):
        cx = x_coords[i]
        if needs_contact(node, pdn_nodes):
            ax.plot(cx, y_pdn, 'ks', markersize=7, zorder=4)
        ax.text(cx, y_pdn - 0.7, node, ha='center', fontsize=8)
        if node not in node_positions: node_positions[node] = []
        node_positions[node].append((cx, y_pdn))
        
        if node == 'GND':
            ax.plot([cx, cx], [y_pdn, y_gnd], color=c_rail, linewidth=1.8)

    # PUN (PMOS) Logic
    for i, node in enumerate(pun_nodes):
        cx = x_coords[i]
        if needs_contact(node, pun_nodes):
            ax.plot(cx, y_pun, 'ks', markersize=7, zorder=4)
        ax.text(cx, y_pun + 0.7, node, ha='center', fontsize=8)
        if node not in node_positions: node_positions[node] = []
        node_positions[node].append((cx, y_pun))
        
        if node == 'VDD':
            ax.plot([cx, cx], [y_pun, y_vdd], color='blue', linewidth=1.8)

    # 5. Connect the Output Node and Internal Straps (Metal 1)
    for node, pos_list in node_positions.items():
        if node in ['VDD', 'GND']: continue
        pos_list.sort()
        
        if node == output_node:
            min_x, max_x = min(p[0] for p in pos_list), max(p[0] for p in pos_list)
            ax.plot([min_x, max_x], [y_out, y_out], color=c_metal_out, linewidth=1.8)
            ax.text(max_x + 0.4, y_out, f"Output ({node})", color=c_metal_out, fontweight='bold', fontsize=10)
            for px, py in pos_list:
                ax.plot([px, px], [py, y_out], color=c_metal_out, linewidth=1.8)
        
        elif len(pos_list) > 1:
            for j in range(len(pos_list) - 1):
                p1, p2 = pos_list[j], pos_list[j+1]
                bridge_y = p1[1] + 0.4 if p1[1] == y_pdn else p1[1] - 0.4
                ax.plot([p1[0], p1[0], p2[0], p2[0]], [p1[1], bridge_y, bridge_y, p2[1]], 
                        color=c_metal_int, linewidth=1.2)

    # 6. Legend - placed outside the plot area to avoid overlap
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    
    legend_elements = [
        Patch(facecolor=c_pdiff, edgecolor='none', label='p-diffusion (PMOS)'),
        Patch(facecolor=c_ndiff, edgecolor='none', label='n-diffusion (NMOS)'),
        Line2D([0], [0], color=c_poly, linewidth=3, label='Polysilicon Gate'),
        Line2D([0], [0], color='blue', linewidth=3, label='Metal (VDD Rail)'),
        Line2D([0], [0], color=c_rail, linewidth=3, label='Metal (GND Rail)'),
        Line2D([0], [0], color=c_metal_out, linewidth=2, label='Metal 1 (Output)'),
        Line2D([0], [0], color=c_metal_int, linewidth=2, label='Metal 1 (Internal)'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor=c_contact, markersize=8, label='Contact')
    ]
    
    # Place legend outside the plot on the right side
    ax.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1.02, 0.5),
              fontsize=9, frameon=True, edgecolor='gray', fancybox=False)

    ax.set_xlim(-2.5, x_coords[-1] + 2)
    ax.set_ylim(-1, 10)
    ax.axis('off')
    plt.title(f"Optimized CMOS Stick Diagram\nGate Sequence: {'-'.join(consistent_path)}", fontsize=13)
    plt.tight_layout()
    plt.show()
# PUN: (Source, Drain, Gate)
pun_edges = [
    ('VDD', 'I', 'A'),
    ('VDD', 'I', 'C'),
    ('VDD', 'F', 'B'),
    ('I','F','D')
]

# pun_edges = [
#     ('VDD', 'I', 'A'),
#     ('VDD', 'J', 'C'),
#     ('J', 'X', 'D'), # Note: Labels like GND/VDD are just node names here
#     ('I', 'X', 'B')
# ]

# # PDN: (Source, Drain, Gate)
# pdn_edges = [
#     ('GND', 'J', 'C'),
#     ('J', 'I', 'B'),
#     ('I', 'F', 'A')
# ]
pdn_edges = [
    ('GND', 'K', 'C'),
    ('K', 'J', 'A'),
    ('GND', 'J', 'D'),
    ('J', 'F', 'B')
]

# valid_paths_pdn = get_euler_circuit(pdn_edges,'F')
valid_paths_pdn = find_best_euler_path(pdn_edges)
valid_paths_pun = find_best_euler_path(pun_edges)

draw_network(pun_edges, title ="Pull Up Network Graph")
draw_network(pdn_edges, title = "Pull Down Network Graph")


consistent_path = find_consistent_path(valid_paths_pun,valid_paths_pdn)

pun_node_path = generate_full_node_path(pun_edges,consistent_path)
pdn_node_path = generate_full_node_path(pdn_edges,consistent_path)

plot_stick_diagram(consistent_path,pun_node_path,pdn_node_path,output_node='F')