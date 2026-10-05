import re
import pandas as pd
import plotly.express as px
from collections import defaultdict
import os
import numpy as np
from scipy.optimize import curve_fit
import plotly.graph_objects as go
import pickle
import matplotlib.pyplot as plt
import json

def parse_ga_log(file_path):
    times_by_nodes = defaultdict(list)
    current_nodes = None
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('Testing with'):
                match = re.search(r'Testing with (\d+) nodes:', line)
                if match:
                    current_nodes = int(match.group(1))
            elif line.startswith('Time:') and current_nodes is not None:
                time_match = re.search(r'Time: ([\d\.]+)s', line)
                if time_match:
                    time_ms = float(time_match.group(1)) * 1000
                    times_by_nodes[current_nodes].append(time_ms)
    return times_by_nodes

def parse_qaoa_GC_log(file_path):
    times_by_nodes = defaultdict(list)
    current_nodes = None
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if 'Nodes' in line:
                match = re.search(r'Nodes:', line)
                if match:
                    current_nodes = int(match.group(1))
    return times_by_nodes

def parse_json_log(file_path):
    """
    Parse QAOA experiment log in JSON format.
    Returns: dict {node_count: [list of times in ms]}
    """
    times_by_nodes = defaultdict(list)
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Expecting top-level key 'experiment_data'
    exp_data = data.get('experiment_data', {})
    for node_str, record in exp_data.items():
        node_count = int(node_str)
        # Use total_time or real_execution_time as needed; here we use total_time
        real_time = float(record['real_execution_time'])
        times_by_nodes[node_count].append(real_time)
    return times_by_nodes

def parse_qaoa_simulated_log(file_path):
    """
    Parse QAOA log file and return:
      1. Average duration per entry (ms) for each node count
      2. Total estimated time (ms), scaled by p-level and iterations, for each node count
    Returns:
      total_time_by_nodes: defaultdict(list)
      avg_entry_time_by_nodes: defaultdict(list)
    """
    times_by_nodes = defaultdict(list)
    optimisation_times_by_nodes = defaultdict(list)
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Process and compute values
    for experiment_id, entry in data["experiment_data"].items():
        try:
            optimization_time = float(entry["real_execution_time"])
            est_time_per_iter = int(entry["circuit_execution_estimated_time(ns)"])
            iterations = int(entry["iterations"])
            total_est_time = (est_time_per_iter * iterations)/1000000
            times_by_nodes[int(experiment_id)].append(total_est_time)
            optimisation_times_by_nodes[int(experiment_id)].append(((optimization_time * iterations)*1000))
        except KeyError as e:
            print(f"Experiment {int(experiment_id)} missing key: {e}")
    return optimisation_times_by_nodes,times_by_nodes

def parse_qaoa_simulated1_log(file_path):
    """
    Parse QAOA log file and return:
      1. Average duration per entry (ms) for each node count
      2. Total estimated time (ms), scaled by p-level and iterations, for each node count
    Returns:
      total_time_by_nodes: defaultdict(list)
      avg_entry_time_by_nodes: defaultdict(list)
    """
    times_by_nodes = defaultdict(list)
    avg_times_by_nodes = defaultdict(list)
    stats = defaultdict(list)
    with open(file_path, 'r') as f:
        data = json.load(f)

    data = data["experiment_data"]

    for key, entry in data.items():
        node_num = key.split("_")[0]  # Extract '2' from '2_1'
        current_exec_time = float(entry['real_execution_time'])
        current_iterations = int(entry['iterations'])
        stats[node_num].append({
            'real_time' : current_exec_time,
            'iterations': current_iterations
        })
        # Process and compute values
    for node_count, runs in stats.items():
        try:
            avg_time = (sum(run['real_time'] for run in runs) / len(runs))*1000
            avg_times_by_nodes[node_count].append(avg_time)
            for run in runs:
                total_time = (run['real_time'] * run['iterations'])
                # total_time = (sum(run['total_time_ns'] * 500 * run['iterations'] for run in runs))
                times_by_nodes[node_count].append(total_time)
        except KeyError as e:
            print(f"Experiment {int(node_count)} missing key: {e}")
    return avg_times_by_nodes,times_by_nodes


def parse_csv_log(file_path):
    df = pd.read_csv(file_path)
    times_by_nodes = defaultdict(list)
    # Some CSVs may have an extra space in the column name
    col_name = ' execution time [ns]' if ' execution time [ns]' in df.columns else 'execution time [ns]'
    for _, row in df.iterrows():
        nodes = int(row['Number of vertices'])
        time_ns = int(row[col_name])
        time_ms = time_ns / 1e6
        times_by_nodes[nodes].append(time_ms)
    return times_by_nodes

def parse_sat_mcs_log(file_path, algorithm):
    times_by_nodes = defaultdict(list)
    current_nodes = None
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    for line in lines:
        if algorithm.upper() == 'SAT' or "SAT" in algorithm.upper():
            if "c Stats: Instance" in line:
                match = re.search(r"ER(\d+)\..*?\.col", line)
                if match:
                    current_nodes = int(match.group(1))
            elif "Stats: Time" in line and "Total:" in line:
                time_ms = 0
                seconds_match = re.search(r'(\d+)s', line)
                if seconds_match:
                    time_ms += float(seconds_match.group(1)) * 1000
                ms_match = re.search(r'(\d+)ms', line)
                if ms_match:
                    time_ms += float(ms_match.group(1))
                if (seconds_match or ms_match) and current_nodes is not None:
                    times_by_nodes[current_nodes].append(time_ms)
        else:
            match_nodes = re.search(r'NUMBER OF NODES (\d+)', line)
            if match_nodes:
                current_nodes = int(match_nodes.group(1))
            match_time = re.search(r'(\d+)ns', line)
            if match_time and current_nodes:
                time_ms = int(match_time.group(1)) / 1e6
                times_by_nodes[current_nodes].append(time_ms)
    return times_by_nodes

def parse_pickle_log(file_path):
    times_by_nodes = defaultdict(list)
    current_nodes = None
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    # Shows the type of object stored
    data = data['COBYLA']
    current_nodes = data.keys()

    for i in current_nodes:
        times_by_nodes[i].append((np.sum(data[i]['qaoa_simulation_time']))*1000)

    return times_by_nodes 

def parse_algorithm_log(file_path, algorithm):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == '.csv':
        return parse_csv_log(file_path)
    if ext == '.pkl':
        return parse_pickle_log(file_path)
    with open(file_path, 'r') as f:
        first_lines = [f.readline() for _ in range(5)]
        f.seek(0)
        content = f.read()
    if 'GA TSP' in ''.join(first_lines):
        return parse_ga_log(file_path)
    if algorithm == 'QAOA':
        return parse_qaoa_simulated1_log(file_path)
    if 'c Stats: Instance' in content or 'NUMBER OF NODES' in content or 'ns' in content:
        return parse_sat_mcs_log(file_path, algorithm)
    try:
        return parse_csv_log(file_path)
    except Exception:
        return defaultdict(list)

# Define theoretical complexity functions for each algorithm
def get_theoretical_complexity_function(algorithm):
    """
    Returns a function that computes the theoretical time complexity for a given algorithm.
    """
    complexity_functions = {
        'GA': lambda n: n**2,  # Quadratic for genetic algorithms
        'BranchAndBound': lambda n: 2**n,  # Exponential worst case for TSP
        'SimulatedAnnealing': lambda n: n**2,  # Polynomial (depends on cooling schedule)
        'HeldKarp': lambda n: n**2 * 2**n,  # Dynamic programming TSP
        'QAOA': lambda n: n**2,  # Polynomial for quantum approximate algorithms
    }
    
    return complexity_functions.get(algorithm, lambda n: n**2)  # Default to quadratic

def fit_theoretical_complexity_and_project(x, y, x_proj, algorithm, fit_law='power'):
    """
    Fit actual data to a chosen extrapolation law and project using the model.
    fit_law: 'power', 'linear', 'quadratic', 'exponential', 'log'
    """
    # x = np.array(x)
    # y = np.array(y)
    # x_proj = np.array(x_proj)

    x = np.array(x).astype(float)
    y = np.array(y).astype(float)
    x_proj = np.array(x_proj).astype(float)

    if len(x) == 0:
        return np.zeros_like(x_proj)
    
    # Get theoretical complexity function
    complexity_func = get_theoretical_complexity_function(algorithm)
    try:
        if complexity_func is not None:
            theoretical_x = np.array([complexity_func(n) for n in x])
            if len(x) >= 2:
                c = np.sum(y * theoretical_x) / np.sum(theoretical_x**2)
            else:
                c = y[0] / theoretical_x[0] if theoretical_x[0] > 0 else 0
            theoretical_proj = np.array([complexity_func(n) for n in x_proj])
            y_proj = c * theoretical_proj
        else:
            # Define fitting laws
            def power_law(x, a, b): return a * (x ** b)
            def linear_law(x, a, b): return 10**((a * x) + b)
            def quadratic_law(x, a, b, c): return a * x**2 + b * x + c
            def exponential_law(x, a, b): return a * np.exp(b * x)
            def log_law(x, a, b): return a * np.log(x) + b
            def theo(n,a): return a*n**2

            # Select fitting law
            if fit_law == 'power':
                func = power_law
                p0 = [1.0, 1.0]
            elif fit_law == 'linear':
                func = linear_law
                p0 = [1.0, 0.0]
            elif fit_law == 'quadratic':
                func = quadratic_law
                p0 = [1.0, 1.0, 0.0]
            elif fit_law == 'exponential':
                func = exponential_law
                p0 = [1.0, 0.01]
            elif fit_law == 'log':
                func = log_law
                p0 = [1.0, 0.0]
                # Avoid log(0) or log(negative)
                x = x[x > 0]
                y = y[:len(x)]
                x_proj = x_proj[x_proj > 0]
            elif fit_law == 'theo':
                func = theo
                p0=[1.0]
            else:
                raise ValueError(f"Unknown fit law: {fit_law}")

            popt, _ = curve_fit(func, x, y, p0=p0, maxfev=10000)
            y_proj = func(x_proj, *popt)
        
        y_proj = np.clip(y_proj, 0, None)
        return y_proj
        
    except Exception as e:
        print(f"Error in fitting for {algorithm} ({fit_law}): {e}")
        # Fallback to linear extrapolation if fitting fails
        if len(x) > 1:
            coeffs = np.polyfit(x, y, 1)
            y_proj = np.polyval(coeffs, x_proj)
        else:
            y_proj = np.full_like(x_proj, y[0] if len(y) > 0 else 0)
        return np.clip(y_proj, 0, None)

def prepare_actual_data(data_dict):
    """Prepare actual experimental data for plotting"""
    rows = []
    
    for algo, times_by_nodes in data_dict.items():
        existing_nodes = sorted(times_by_nodes.keys())
        
        for n in existing_nodes:
            times = times_by_nodes[n]
            avg = np.mean(times)
            ci = 1.96 * np.std(times, ddof=1)/np.sqrt(len(times)) if len(times) > 1 else 0
            rows.append({
                'Algorithm': algo,
                'Nodes': n,
                'AverageTime': avg,
                'CI_plus': ci,
                'CI_minus': ci,
                'MinTime': min(times),
                'MaxTime': max(times)
            })
    
    return pd.DataFrame(rows)

def prepare_theoretical_data(data_dict, node_range=(1, 51), fit_laws=['power']):
    """Prepare theoretical projections for all algorithms across full node range"""
    start_node, end_node = node_range
    all_nodes = list(range(start_node, end_node))
    rows = []

    for algo, times_by_nodes in data_dict.items():
        existing_nodes = sorted(times_by_nodes.keys())
        if not existing_nodes:
            continue

        existing_means = [np.mean(times_by_nodes[n]) for n in existing_nodes]

        # Handle multiple fit laws only for qaoa_actual
        if algo == 'QAOA':
            laws_to_apply = ['linear','theo']
        else:
            laws_to_apply = fit_laws

        for law in laws_to_apply:
            projected_times = fit_theoretical_complexity_and_project(
                existing_nodes,
                existing_means,
                all_nodes,
                algo,
                fit_law=law
            )

            for i, n in enumerate(all_nodes):
                label = f"{algo} {law}" if algo == 'QAOA' else algo
                rows.append({
                    'Algorithm': label,
                    'Nodes': n,
                    'TheoreticalTime': projected_times[i]
                })

    return pd.DataFrame(rows)

def create_actual_times_plot_matplotlib(df_actual):
    import matplotlib.pyplot as plt

    algorithms = df_actual['Algorithm'].unique()
    colors = plt.cm.get_cmap('tab10', len(algorithms))

    plt.figure(figsize=(12, 7))

    for i, algo in enumerate(algorithms):
        algo_data = df_actual[df_actual['Algorithm'] == algo].sort_values('Nodes')
        x = algo_data['Nodes']
        y = algo_data['AverageTime']
        yerr = algo_data['CI_plus']

        plt.errorbar(
            x, y, yerr=yerr,
            fmt='-o', label=f"{algo}",
            color=colors(i), capsize=5
        )

    plt.yscale("log")
    plt.xlabel("Number of Nodes", fontsize=14)
    plt.ylabel("Average Time (ms, log scale)", fontsize=14)
    plt.title("Actual Algorithm Performance", fontsize=16)
    plt.grid(True, linestyle='--', linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    # plt.savefig("actual_algorithm_performance_matplotlib.png")
    plt.show()


def create_theoretical_plot_matplotlib(df_theoretical):
    import matplotlib.pyplot as plt

    algorithms = df_theoretical['Algorithm'].unique()
    colors = plt.cm.get_cmap('tab10', len(algorithms))

    plt.figure(figsize=(12, 7))
    skip_algos = ['GA', 'SimulatedAnnealing']

    for i, algo in enumerate(algorithms):
        if algo in skip_algos:
            continue
        algo_data = df_theoretical[df_theoretical['Algorithm'] == algo].sort_values('Nodes')
        x = algo_data['Nodes']
        y = algo_data['TheoreticalTime']

        plt.plot(
            x, y, '--o',
            label=f"{algo}",
            color=colors(i)
        )

    plt.yscale("log")
    plt.xlabel("Number of Nodes", fontsize=14)
    plt.ylabel("Projected Theoretical Time (ms, log scale)", fontsize=14)
    plt.title("Theoretical Complexity Projections", fontsize=16)
    plt.grid(True, linestyle='--', linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    # plt.savefig("theoretical_algorithm_complexity_matplotlib.png")
    plt.show()


def create_combined_plot_matplotlib(df_actual, df_theoretical):
    import matplotlib.pyplot as plt

    algorithms = sorted(set(df_actual['Algorithm'].unique()) | set(df_theoretical['Algorithm'].unique()))
    colors = plt.cm.get_cmap('tab10', len(algorithms))

    plt.figure(figsize=(14, 8))

    for i, algo in enumerate(algorithms):
        color = colors(i)
        actual_data = df_actual[df_actual['Algorithm'] == algo].sort_values('Nodes')
        theoretical_data = df_theoretical[df_theoretical['Algorithm'] == algo].sort_values('Nodes')

        if not actual_data.empty:
            plt.errorbar(
                actual_data['Nodes'],
                actual_data['AverageTime'],
                yerr=actual_data['CI_plus'],
                fmt='-o',
                label=f"{algo}",
                color=color,
                capsize=4
            )

        if not theoretical_data.empty:
            plt.plot(
                theoretical_data['Nodes'],
                theoretical_data['TheoreticalTime'],
                '--',
                label=f"{algo}",
                color=color
            )

    plt.yscale("log")
    plt.xlabel("Number of Nodes", fontsize=14)
    plt.ylabel("Time (ms, log scale)", fontsize=14)
    plt.title("Algorithm Performance: Actual vs Theoretical", fontsize=16)
    plt.grid(True, linestyle='--', linewidth=0.5)
    plt.legend()
    plt.tight_layout()
    # plt.savefig("combined_algorithm_plot_matplotlib.png")
    plt.show()

def create_all_plots_panel(df_actual, df_theoretical, save_path='algorithm_panel_plot.pdf'):
    algorithms = sorted(set(df_actual['Algorithm'].unique()) | set(df_theoretical['Algorithm'].unique()))
    cmap = plt.cm.get_cmap('tab10', len(algorithms))

    fig, axs = plt.subplots(1, 3, figsize=(16,4), sharex=False,sharey=False)
    labels = ['(a)', '(b)', '(c)']
    titles = ['Actual Performance', 'Theoretical Complexity', 'Actual vs Theoretical']
    skip_algos = ['GA', 'SimulatedAnnealing','qaoa_sim_estimated','Actual_quantum_times','QAOA linear','total_quantum_times','average_quantum_times']
    include_algos =['QAOA','qaoa_actual']


    # Plot (a): Actual Performance
    # ax = axs[0]
    # for i, algo in enumerate(df_actual['Algorithm'].unique()):
    #     algo_data = df_actual[df_actual['Algorithm'] == algo].sort_values('Nodes')
    #     ax.errorbar(
    #         algo_data['Nodes'], algo_data['AverageTime'],
    #         yerr=algo_data['CI_plus'],
    #         fmt='-o', label=algo,
    #         color=cmap(i), capsize=3, markersize=5
    #     )
    # ax.set_yscale('log')
    # ax.set_xlabel("Number of Nodes", fontsize=12)
    # ax.set_ylabel("Avg Time (ms)", fontsize=12)
    # # ax.set_title(f'{labels[0]} {titles[0]}', loc='left', fontsize=14, weight='bold')
    # ax.grid(True, linestyle='--', linewidth=0.5)
    # ax.legend(fontsize=8)

    # Plot (b): Theoretical Complexity
    ax = axs[0]
    for i, algo in enumerate(df_theoretical['Algorithm'].unique()):
        if algo in skip_algos:
            continue
        algo_data = df_theoretical[df_theoretical['Algorithm'] == algo].sort_values('Nodes')
        if algo == 'QAOA theo':
            algo = 'QAOA(proj)'
        if algo == "QAOA_sim":
            algo="QAOA(proj)"
        ax.plot(
            algo_data['Nodes'], algo_data['TheoreticalTime'],
            '--o', label=f'{algo}',
            color=cmap(i), markersize=5
        )
    ax.set_yscale('log')
    ax.set_xlabel("Number of Nodes", fontsize=16)
    ax.set_ylabel("Time Complexity (log)", fontsize=14)
    # ax.set_title(f'{labels[1]} {titles[1]}', loc='left', fontsize=14, weight='bold')
    ax.grid(True, linestyle='--', linewidth=0.5)
    ax.legend(fontsize=12)
    ax.text(0.02, 0.95, '(a)', transform=ax.transAxes, fontsize=18, 
            fontweight='bold', verticalalignment='top')

    # Plot (c): Combined
    ax = axs[1]
    skip_algos = ['Actual_quantum_times','qaoa_sim_estimated', 'total_quantum_times', 'average_quantum_times']
    for i, algo in enumerate(algorithms):
        if algo in skip_algos:
            continue
        color = cmap(i)
        actual_data = df_actual[df_actual['Algorithm'] == algo].sort_values('Nodes')
        theoretical_data = df_theoretical[df_theoretical['Algorithm'] == algo].sort_values('Nodes')

        if not actual_data.empty:
            ax.errorbar(
                actual_data['Nodes'], actual_data['AverageTime'],
                yerr=actual_data['CI_plus'],
                fmt='-o' if algo not in ['HeldKarp', 'SimulatedAnnealing'] else 'D', label=f"{algo}" if algo != "QAOA_sim" else 'QAOA(proj)',
                color=color if algo !='SimulatedAnnealing'else '#9a0e8e', capsize=3, markersize=5 if algo not in ['HeldKarp', 'SimulatedAnnealing'] else 3)

    qaoa_data = df_actual[df_actual['Algorithm'] == 'QAOA_sim'].sort_values('Nodes')
    print(qaoa_data)
    if len(qaoa_data) >= 2:
        x = qaoa_data['Nodes'].values
        y = qaoa_data['AverageTime'].values
        x = np.array(x, dtype=float)
        
        # Fit log10(y) = a*x + b
        logy = np.log10(y)
        logy = np.array(logy, dtype=float)
        a, b = np.polyfit(x, logy, 1)

        # Project up to 60 nodes
        x_proj = np.arange(x.min(), 61)  # or 51 if you want up to 51
        y_proj = 10**(a * x_proj + b)

        # Define the model: y = c * n^5
        def n5_model(n, c):
            return (c * n**5)

        # Fit the model to your data
        popt, _ = curve_fit(n5_model, x, y)
        c_fit = popt[0]
        print(c_fit)

        # Project up to 61 nodes
        x_proj1 = np.arange(x.min(), 101)
        y_proj_n5 = n5_model(x_proj1, c_fit)


        # Plot actual data and projection
        # ax.plot(x_proj, y_proj, color="#7dbdec", linestyle='--', linewidth=2, 
        #         label=r'QAOA (proj.exp)')
        
        ax.plot(x_proj1, y_proj_n5, color="#9a0e8e", linestyle='--', linewidth=2, 
                label=r'QAOA(proj)')

    ax.set_yscale('log')
    ax.set_xlabel("Number of Nodes", fontsize=16)
    axs[1].set_ylabel("Log Time (ms)", fontsize=14)
    # ax.set_title(f'{labels[2]} {titles[2]}', loc='left', fontsize=14, weight='bold')
    ax.grid(True, linestyle='--', linewidth=0.5)    
    ax.legend(loc='lower right',fontsize=12)
    ax.text(0.02, 0.95, '(b)', transform=ax.transAxes, fontsize=18, 
            fontweight='bold', verticalalignment='top')

    # Plot (b): Theoretical Complexity
    ax = axs[2]
    skip_algos =['GA','BranchAndBound','SimulatedAnnealing','HeldKarp']
    for i, algo in enumerate(df_actual['Algorithm'].unique()):
        algo1=''
        if algo in skip_algos:
            continue
        if algo=='average_quantum_times':
            algo1='QAOA_sim'
        
        elif algo=='QAOA_sim':
            # algo1 = 'QAOA_sim_1iter'
            continue
        algo_data = df_actual[df_actual['Algorithm'] == algo].sort_values('Nodes')
        ax.plot(
            algo_data['Nodes'], algo_data['AverageTime'],
            '--o', label=f'{algo1}',
            color=cmap(i), markersize=5
        )
        if algo == 'total_quantum_times':
            algo1 ='QAOA_real'
            algo_data = df_actual[df_actual['Algorithm'] == algo].sort_values('Nodes')
            ax.errorbar(
                algo_data['Nodes'], algo_data['AverageTime'],
                yerr=algo_data['CI_plus'],
                fmt='-o' , label=f"{algo1}",
                color=cmap(i), capsize=3, markersize= 5)
            continue
    ax.set_yscale('log')
    ax.set_xlabel("Number of Nodes", fontsize=16)
    ax.set_ylabel("Time (log) ms", fontsize=14)
    # ax.set_title(f'{labels[1]} {titles[1]}', loc='left', fontsize=14, weight='bold')
    ax.grid(True, linestyle='--', linewidth=0.5)
    ax.legend(fontsize=12)
    ax.text(0.02, 0.95, '(c)', transform=ax.transAxes, fontsize=18, 
            fontweight='bold', verticalalignment='top')

    # General formatting
    for ax in axs:
        ax.tick_params(axis='both', which='major', labelsize=14)
        # ax.label_outer()

    plt.tight_layout()
    # plt.savefig(save_path, bbox_inches='tight')
    # print(f"Saved 3-panel plot to '{save_path}'")
    plt.show()

    
def main():
    log_files = {
        'GA': 'tsp_GA_data',
        'BranchAndBound': 'tsp_branch_and_bound_data.csv',
        'SimulatedAnnealing': 'tsp_sim_annealing_data.csv',
        'HeldKarp': 'tsp_held_karp_results.csv',
        'QAOA_sim': 'quantum_tsp_results_final.pkl',
        'QAOA': 'experiment_data_sorted.json'
    }

    # Parse data
    data = {}
    # QAOA simulated
    # if os.path.exists(log_files['qaoa_sim']):
    #     qaoa_sim_total, qaoa_sim_avg = parse_qaoa_simulated_log(log_files['qaoa_sim'])
    #     data['qaoa_sim_total'] = qaoa_sim_total
    #     data['qaoa_sim_avg'] = qaoa_sim_avg
    for algo, path in log_files.items():
        if os.path.exists(path):
            if algo=='QAOA':
                qaoa_sim_total,qaoa_sim_est =  parse_algorithm_log(path, algo)
                data['average_quantum_times'] = qaoa_sim_total
                data['total_quantum_times'] = qaoa_sim_est
            else:
                data[algo] = parse_algorithm_log(path, algo)
        else:
            print(f"Warning: File not found for {algo}: {path}")

    # Prepare separate datasets
    df_actual = prepare_actual_data(data)
    df_theoretical = prepare_theoretical_data(data, node_range=(1, 51))

    print(f"Actual data points: {len(df_actual)}")
    print(f"Theoretical data points: {len(df_theoretical)}")
    print(f"Algorithms with actual data: {df_actual['Algorithm'].unique()}")
    print(f"Algorithms with theoretical projections: {df_theoretical['Algorithm'].unique()}")

    # Create separate plots
    # create_actual_times_plot_matplotlib(df_actual)
    # create_theoretical_plot_matplotlib(df_theoretical)
    # create_combined_plot_matplotlib(df_actual, df_theoretical)
    create_all_plots_panel(df_actual, df_theoretical)


def plot_num_qbits_vs_nodes():
    # Original known data points
    x_known = np.array([4, 5, 6, 7, 8])
    y_known = np.array([2, 3, 3, 4, 4])

    # Interpolation range
    x_interp = np.arange(4, 9)  # 4 to 8 inclusive
    y_interp = np.interp(x_interp, x_known, y_known)
    y1_interp = np.abs(np.ceil(x_interp * np.log(y_interp)))

    # Extrapolation range
    x_extra = np.arange(9, 101)
    # Use last two known points to extrapolate linearly
    slope = (y_known[-1] - y_known[-2]) / (x_known[-1] - x_known[-2])
    y_extra = y_known[-1] + slope * (x_extra - x_known[-1])
    y1_extra = np.abs(np.ceil(x_extra * np.log(y_extra)))

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.xlabel("Number of Nodes")
    plt.ylabel("Number of Qubits")
    plt.title("Interpolated vs Extrapolated Qubit Projection")

    # Interpolated part (solid line)
    plt.plot(x_interp, y1_interp, 'o-', label="Interpolated", color='blue')

    # Extrapolated part (dashed line)
    plt.plot(x_extra, y1_extra, 'o--', label="Extrapolated", color='orange')

    plt.grid(True)
    plt.legend()
    plt.show()

if __name__ == "__main__":
   main()
    # print(parse_qaoa_simulated1_log("./experiment_data_sorted.json"))