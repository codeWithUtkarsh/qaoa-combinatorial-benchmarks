import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import defaultdict
import os
import numpy as np
from scipy.optimize import curve_fit
import pickle
import json
from matplotlib.patches import Rectangle

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

def parse_qaoa_simulated_log(file_path):
    """
    Parse QAOA log file and return:
      1. Average duration per entry (ms) for each node count
      2. Total estimated time (ms), scaled by p-level and iterations, for each node count
    Returns:
      total_time_by_nodes: defaultdict(list)
      avg_entry_time_by_nodes: defaultdict(list)
    """
    # Patterns
    node_pat = re.compile(r"Running QAOA with p=(\d+), Node: (\d+), Shots: (\d+)")
    total_time_pat = re.compile(r"total estimated time for all runs ([\d\.eE+-]+)")
    iter_pat = re.compile(r"total iterations for all runs (\d+)")

    # Store all entries for each node count
    entries = defaultdict(list)

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_nodes = None
    current_p_level = None
    current_total_time = None
    current_iterations = None

    for line in lines:
        node_match = node_pat.search(line)
        if node_match:
            current_p_level = int(node_match.group(1))
            current_nodes = int(node_match.group(2))
            current_total_time = None
            current_iterations = None
            continue

        total_time_match = total_time_pat.search(line)
        if total_time_match:
            current_total_time = float(total_time_match.group(1))  # in ns
            continue

        iter_match = iter_pat.search(line)
        if iter_match:
            current_iterations = int(iter_match.group(1))
            if (
                current_nodes is not None
                and current_total_time is not None
                and current_p_level is not None
            ):
                entries[current_nodes].append({
                    'total_time_ns': current_total_time,
                    'p_level': current_p_level,
                    'iterations': current_iterations
                })
                current_total_time = None
                current_iterations = None

    avg_entry_time_by_nodes = defaultdict(list)
    total_time_by_nodes = defaultdict(list)

    for node_count, runs in entries.items():
        # Average duration per entry (convert ns to ms)
        avg_entry_time = (sum(run['total_time_ns'] for run in runs) / len(runs))*1000
        avg_entry_time_by_nodes[node_count].append(avg_entry_time)

        # Total estimated time (sum over all runs, each scaled by p_level * iterations)
        total_time = (sum(run['total_time_ns'] * run['iterations'] for run in runs))
        total_time_by_nodes[node_count].append(total_time)
    
    return total_time_by_nodes, avg_entry_time_by_nodes

def parse_qaoa_simulated1_log(file_path):
    """
    Parse QAOA log file and return:
      1. Average duration per entry (ms) for each node count
      2. Total estimated time (ms), scaled by p-level and iterations, for each node count
    Returns:
      total_time_by_nodes: defaultdict(list)
      avg_entry_time_by_nodes: defaultdict(list)
    """
    # Patterns
    node_pat = re.compile(r"Running QAOA with p=(\d+), Node: (\d+), Shots: (\d+)")
    total_time_pat = re.compile(r"total estimated time for all runs ([\d\.eE+-]+)")
    iter_pat = re.compile(r"total iterations for all runs (\d+)")

    # Store all entries for each node count
    entries = defaultdict(list)

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_nodes = None
    current_p_level = None
    current_total_time = None
    current_iterations = None

    for line in lines:
        node_match = node_pat.search(line)
        if node_match:
            current_p_level = int(node_match.group(1))
            current_nodes = int(node_match.group(2))
            current_total_time = None
            current_iterations = None
            continue

        total_time_match = total_time_pat.search(line)
        if total_time_match:
            current_total_time = float(total_time_match.group(1))  # in ns
            continue

        iter_match = iter_pat.search(line)
        if iter_match:
            current_iterations = int(iter_match.group(1))
            if (
                current_nodes is not None
                and current_total_time is not None
                and current_p_level is not None
            ):
                entries[current_nodes].append({
                    'total_time_ns': current_total_time,
                    'p_level': current_p_level,
                    'iterations': current_iterations
                })
                current_total_time = None
                current_iterations = None

    avg_entry_time_by_nodes = defaultdict(list)
    total_time_by_nodes = defaultdict(list)

    for node_count, runs in entries.items():
        # Average duration per entry (convert ns to ms)
        avg_entry_time = (sum(run['total_time_ns'] for run in runs) / len(runs))*1000
        avg_entry_time_by_nodes[node_count].append(avg_entry_time)

        # Total estimated time (sum over all runs, each scaled by p_level * iterations)
        for run in runs:
            total_time = (run['total_time_ns'] * run['iterations']*1000)
            # total_time = (sum(run['total_time_ns'] * 500 * run['iterations'] for run in runs))
            total_time_by_nodes[node_count].append(total_time)
    
    return total_time_by_nodes, avg_entry_time_by_nodes

def parse_qaoa_gc(file_path):
    """
    Parse QAOA graph coloring logs.
    Returns: dict {node_count: [list of times in ms]}
    """
    times_by_nodes = defaultdict(list)
    # Regex to match: 2025-06-13 10:52:05,716 - Nodes: 3  QAOA sim Time - Time: 0.08852920000000004ms, ...
    pattern = re.compile(
        r"Nodes:\s*(\d+)\s+QAOA sim Time - Time:\s*([\d\.eE+-]+)ms"
    )
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                node_count = int(match.group(1))
                time_ms = float(match.group(2))*1000
                times_by_nodes[node_count].append(time_ms)
    return times_by_nodes

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
        if algorithm.upper() == 'SAT':
            if "c Stats: Instance" in line:
                match = re.search(r"ER(\d+)\..*?\.col", line)
                if match:
                    current_nodes = int(match.group(1))
            elif "Stats: Time" in line and "Total:" in line:
                time_ms = 0
                hours_match = re.search(r'(\d+)h',line)
                if hours_match:
                    time_ms += float(hours_match.group(1)) * 3600000
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

def parse_json_log(file_path):
    """
    Parse QAOA experiment log in JSON format.
    Returns: dict {node_count: [list of times in ms]}
    """
    times_by_nodes = defaultdict(list)
    optimisation_times_by_nodes = defaultdict(list)
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Process and compute values
    for experiment_id, entry in data["experiment_data"].items():
        experiment_id = experiment_id.split("_")[0]
        try:
            iterations = int(entry["iteration"])
            optimization_time = float(entry["real_execution_time"])*iterations
            optimisation_times_by_nodes[int(experiment_id)].append(((optimization_time)*1000))
        except KeyError as e:
            print(f"Experiment {int(experiment_id)} missing key: {e}")
    return optimisation_times_by_nodes

def parse_algorithm_log(file_path, algorithm):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == '.csv':
        return parse_csv_log(file_path)
    if ext == '.json':
        return parse_json_log(file_path)
    if ext == '.pkl':
        return parse_pickle_log(file_path)
    if 'qaoa_GC' in algorithm:
        return parse_qaoa_gc(file_path)
    if 'qaoa_sim' in algorithm:
        return parse_qaoa_simulated_log(file_path)
    if 'qaoa_sim1' in algorithm:
        return parse_qaoa_simulated1_log(file_path)
    with open(file_path, 'r') as f:
        first_lines = [f.readline() for _ in range(5)]
        f.seek(0)
        content = f.read()
    if 'GA TSP' in ''.join(first_lines):
        return parse_ga_log(file_path)
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
    If no theoretical complexity is defined, returns None.
    """
    complexity_functions = {
        'SAT': lambda n: 2**n,
        'MCS': lambda n: n**3,
        'LMXRLF': lambda n: n**2,
        'DSATUR': lambda n: n**2,
        # 'QAOA': lambda n: n**5,
    }
    return complexity_functions.get(algorithm, None)

def fit_theoretical_complexity_and_project(x, y, x_proj, algorithm, fit_law='power'):
    """
    Fit actual data to a chosen extrapolation law and project using the model.
    fit_law: 'power', 'linear', 'quadratic', 'exponential', 'log'
    """
    x = np.array(x)
    y = np.array(y)
    x_proj = np.array(x_proj)
    
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
        existing_nodes = existing_nodes[:100]
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
    df=pd.DataFrame(rows)
    print(df[df['Algorithm']=='QAOA linear'])
    return pd.DataFrame(rows)

def create_qaoa_comparison_plot(data_dict):
    """Create a matplotlib plot comparing all QAOA variants"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = {
        'QAOA': '#1f77b4',  # blue
        'QAOA_sim_total': '#ff7f0e',  # orange
        'QAOA_sim_avg': '#2ca02c',  # green
        'qaoa_GC': '#d62728'  # red
    }
    
    line_styles = {
        'QAOA': '-',
        'QAOA_sim_total': '--',
        'QAOA_sim_avg': ':',
        'qaoa_GC': '-.'
    }
    
    marker_styles = {
        'QAOA': 'o',
        'QAOA_sim_total': 's',
        'QAOA_sim_avg': 'D',
        'qaoa_GC': '^'
    }
    
    # Plot each QAOA variant
    for algo_key, times_by_nodes in data_dict.items():
        if not times_by_nodes:  # Skip empty datasets
            continue
            
        existing_nodes = sorted(times_by_nodes.keys())
        avg_times = [np.mean(times_by_nodes[n]) for n in existing_nodes]
        std_times = [np.std(times_by_nodes[n]) if len(times_by_nodes[n]) > 1 else 0 for n in existing_nodes]
        ci_times = [1.96 * std / np.sqrt(len(times_by_nodes[n])) if len(times_by_nodes[n]) > 1 else 0 for n, std in zip(existing_nodes, std_times)]
        
        color = colors.get(algo_key, '#000000')
        line_style = line_styles.get(algo_key, '-')
        marker_style = marker_styles.get(algo_key, 'o')
        
        # Create readable labels
        if algo_key == 'QAOA':
            label = 'QAOA (Actual Hardware)'
        elif algo_key == 'QAOA_sim_total':
            label = 'QAOA Simulation (Total Time)'
        elif algo_key == 'QAOA_sim_avg':
            label = 'QAOA Simulation (Avg Time)'
        elif algo_key == 'qaoa_GC':
            label = 'QAOA Graph Coloring'
        else:
            label = algo_key
        
        ax.errorbar(existing_nodes, avg_times, yerr=ci_times, 
                   color=color, linestyle=line_style, marker=marker_style,
                   markersize=8, linewidth=2, capsize=5, label=label)
    
    ax.set_xlabel('Number of Nodes', fontsize=14)
    ax.set_ylabel('Execution Time (ms)', fontsize=14)
    ax.set_title('QAOA Performance Comparison: Hardware vs Simulation', fontsize=16)
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', fontsize=12)
    
    # Add border
    for spine in ax.spines.values():
        spine.set_linewidth(2)
        spine.set_color('black')
    
    plt.tight_layout()
    return fig

def create_actual_times_plot(df_actual):
    """Create a matplotlib plot showing only actual experimental times"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    algorithms = df_actual['Algorithm'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(algorithms)))
    
    line_styles = ['-', '--', ':', '-.', '-', '--']
    marker_styles = ['o', 's', 'D', '^', 'v', '<']
    skip_algos = []
    
    for i, algo in enumerate(algorithms):
        if algo in skip_algos:
            continue
            
        algo_data = df_actual[df_actual['Algorithm'] == algo].sort_values('Nodes')
        if len(algo_data) == 0:
            continue
        algo_data1 = algo_data.head(10)
        color = colors[i % len(colors)]
        line_style = line_styles[i % len(line_styles)]
        marker_style = marker_styles[i % len(marker_styles)]
        
        ax.errorbar(algo_data1['Nodes'], algo_data1['AverageTime'], 
                   yerr=[algo_data1['CI_minus'], algo_data1['CI_plus']], 
                   color=color, linestyle='-', marker='o',
                   markersize=8, linewidth=2, capsize=2, label=f'{algo}')
    
    ax.set_xlabel('Number of Nodes', fontsize=18)
    ax.set_ylabel('Average log Time (ms)', fontsize=18)
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis='both', which='major', labelsize=16)
    ax.legend(loc='upper left', fontsize=17)
    
    # Add border
    for spine in ax.spines.values():
        spine.set_linewidth(2)
        spine.set_color('black')
    
    plt.tight_layout()
    return fig

def create_theoretical_plot(df_theoretical, df_actual=None):
    """Create a matplotlib plot showing theoretical complexity projections"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    plotted_actual = set()
    algorithms = df_theoretical['Algorithm'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(algorithms)))
    
    line_styles = ['-', '--', ':', '-.', '-', '--']
    marker_styles = ['o', 's', 'D', '^', 'v', '<']
    skip_algos = ["QAOA (power)", 'QAOA_sim_total', 'QAOA_sim_avg']

    for i, algo in enumerate(algorithms):
        color = colors[i % len(colors)]
        line_style = line_styles[i % len(line_styles)]
        marker_style = marker_styles[i % len(marker_styles)]
        
        algo_theoretical = df_theoretical[df_theoretical['Algorithm'] == algo].sort_values('Nodes')

        if algo not in skip_algos:
            # Add projected/theoretical line
            ax.plot(algo_theoretical['Nodes'], algo_theoretical['TheoreticalTime'], 
                   color=color, linestyle='--', linewidth=2, alpha=0.8, 
                   label=f'{algo} (Theoretical)')

        # Add actual data if provided
        if df_actual is not None:
            base_algo = algo.split(' ')[0]
            if base_algo not in plotted_actual and base_algo in df_actual['Algorithm'].unique():
                algo_actual = df_actual[(df_actual['Algorithm'] == base_algo) & 
                                       (df_actual['Nodes'] <= 50)].sort_values('Nodes')
                if algo != "LMXRLF":
                    ax.errorbar(algo_actual['Nodes'], algo_actual['AverageTime'], 
                               yerr=[algo_actual['CI_minus'], algo_actual['CI_plus']], 
                               color=color, linestyle='-', marker=marker_style,
                               markersize=8, linewidth=2, capsize=5, 
                               label=f'{base_algo} (Actual)')
                    plotted_actual.add(base_algo)
    
    ax.set_xlabel('Number of Nodes', fontsize=14)
    ax.set_ylabel('Projected Complexities (log ms)', fontsize=14)
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', fontsize=12)
    
    # Add border
    for spine in ax.spines.values():
        spine.set_linewidth(2)
        spine.set_color('black')
    
    plt.tight_layout()
    return fig

def create_combined_plot(df_actual, df_theoretical):
    """Create a combined matplotlib plot showing both actual and theoretical data"""
    fig, ax = plt.subplots(figsize=(15, 8))
    
    algorithms = set(df_actual['Algorithm'].unique()) | set(df_theoretical['Algorithm'].unique())
    colors = plt.cm.tab10(np.linspace(0, 1, len(algorithms)))
    
    line_styles = ['-', '--', ':', '-.', '-', '--']
    marker_styles = ['o', 's', 'D', '^', 'v', '<']
    
    for i, algo in enumerate(algorithms):
        color = colors[i % len(colors)]
        line_style = line_styles[i % len(line_styles)]
        marker_style = marker_styles[i % len(marker_styles)]
        
        # Add actual data if available
        actual_data = df_actual[(df_actual['Algorithm'] == algo) & 
                               (df_actual['Nodes'] <= 50)].sort_values('Nodes')
        if len(actual_data) > 0:
            ax.errorbar(actual_data['Nodes'], actual_data['AverageTime'], 
                       yerr=[actual_data['CI_minus'], actual_data['CI_plus']], 
                       color=color, linestyle=line_style, marker=marker_style,
                       markersize=8, linewidth=2, capsize=5, 
                       label=f'{algo} (Actual)')
        
        if algo == 'SAT':
            continue
            
        # Add theoretical data if available
        theoretical_data = df_theoretical[df_theoretical['Algorithm'] == algo].sort_values('Nodes')
        if len(theoretical_data) > 0:
            ax.plot(theoretical_data['Nodes'], theoretical_data['TheoreticalTime'], 
                   color=color, linestyle='--', linewidth=2, alpha=0.7, 
                   label=f'{algo} (Theoretical)')
    
    ax.set_xlabel('Number of Nodes', fontsize=14)
    ax.set_ylabel('Time (ms)', fontsize=14)
    ax.set_title('Algorithm Performance: Actual vs Theoretical Complexity', fontsize=16)
    ax.tick_params(axis='both', which='major', labelsize=20)
    ax.set_yscale('log')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', fontsize=12)
    
    # Add border
    for spine in ax.spines.values():
        spine.set_linewidth(2)
        spine.set_color('black')
    
    plt.tight_layout()
    return fig

def main():
    log_files = {
        'QAOA': './experiment_data_CI_backup.json',
        'qaoa_sim1': './GC_data/log_file6',
        'qaoa_sim':'./log_file_experiment1.txt',
        'MCS': 'stat_info_mcs_small',
        'SAT': 'stat_log_file',
        'DSATUR': 'tmp_stat_info_small',
        'LMXRLF': 'tmp_stat_info_small2',
    }

    # Parse data
    data = {}

    # QAOA actual (hardware)
    if os.path.exists(log_files['QAOA']):
        data['QAOA'] = parse_algorithm_log(log_files['QAOA'], 'QAOA')

    # QAOA simulated
    if os.path.exists(log_files['qaoa_sim']):
        qaoa_sim_total, qaoa_sim_avg = parse_qaoa_simulated_log(log_files['qaoa_sim'])
        data['QAOA_sim_total'] = qaoa_sim_total
        data['QAOA_sim_avg'] = qaoa_sim_avg

    # QAOA simulated
    if os.path.exists(log_files['qaoa_sim1']):
        qaoa_sim1_total, qaoa_sim1_avg = parse_qaoa_simulated1_log(log_files['qaoa_sim1'])
        data['qaoa_sim1_total'] = qaoa_sim1_total
        data['qaoa_sim1_avg'] = qaoa_sim1_avg

    # Parse other algorithms
    for algo in ['DSATUR', 'LMXRLF','MCS','SAT']:
        if os.path.exists(log_files[algo]):
            data[algo] = parse_algorithm_log(log_files[algo], algo)

    # Prepare actual and theoretical data
    df_actual = prepare_actual_data(data)
    df_theoretical = prepare_theoretical_data(data, node_range=(3, 51))

    # fig = (create_actual_times_plot(df_actual=df_actual))
    # fig.savefig('first_fig.png')

    # Create subplot layout: 2 columns (Actual, Theoretical)
    # Set publication-quality style

    # Set publication-quality style
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 9,
        'font.family': 'sans-serif',
        'font.sans-serif': ['Arial', 'DejaVu Sans'],
        'lines.linewidth': 2.0,
        'lines.markersize': 6,
        'axes.linewidth': 1.0,
        'xtick.major.size': 4,
        'ytick.major.size': 4,
        'legend.frameon': True,
        'legend.fancybox': True,
        'legend.shadow': False,
        'legend.framealpha': 0.9,
        'axes.grid': True,
        'grid.alpha': 0.3,
        'grid.linewidth': 0.5
    })

    # Create figure with 1x3 subplots
    fig, ((ax1, ax2, ax3)) = plt.subplots(1, 3, figsize=(16, 4))
    # fig.suptitle('Algorithm Performance Analysis', fontsize=16, fontweight='bold', y=0.95)

    # Define colors for consistency across plots
    colors = {
        'QAOA': '#1f77b4',
        'MCS': '#ff7f0e', 
        'SAT': '#2ca02c',
        'DSATUR': '#d62728',
        'LMXRLF': '#9467bd',
        'QAOA_sim_total': '#8c564b',
        'QAOA_sim_avg': '#e377c2'
    }

    # Plot 1 (Top Left): Main Algorithm Performance Comparison
    algorithms = df_actual['Algorithm'].unique()
    skip_algos = ['QAOA_sim_total', 'QAOA_sim_avg', 'qaoa_sim1_total', 'qaoa_sim1_avg']

    for algo in algorithms:
        if algo in skip_algos:
            continue
        
        if algo in ['DSATUR', 'LMXRLF']:
            # Only the first 100 points for DSATUR and LMXRLF, sorted by node count
            algo_data = df_actual[df_actual['Algorithm'] == algo].sort_values('Nodes')
            # algo_data = df_actual.head(15)
        else:
            algo_data = df_actual[df_actual['Algorithm'] == algo].sort_values('Nodes')
        if len(algo_data) == 0:
            continue
        print(algo)
        color = colors.get(algo, '#1f77b4')
        # Plot actual data with error bars
        x_vals = algo_data['Nodes'].values
        # Apply custom x-offsets only for actual plots (subplot ax1)
        if algo == 'DSATUR':
            x_vals = x_vals + np.where(x_vals < 20, 0.5, 0.2)  # Stronger shift for small nodes
        elif algo == 'MCS':
            x_vals = x_vals - np.where(x_vals < 20, 0.5, 0.2) # Offset MCS nodes slightly the other way
        if algo == 'SAT':
            last_idx = algo_data.index[-1]
            algo_data.loc[last_idx, ['CI_minus']] *= 0.7   # reduce by 70%

        # Plot actual data with error bars
        ax2.errorbar(algo_data['Nodes'], algo_data['AverageTime'],
                    yerr=[algo_data['CI_minus'], algo_data['CI_plus']],
                    color=color, linestyle='-', # In ax1.errorbar call
                    marker='D' if algo == 'DSATUR' else 'o', 
                    markersize=7 if algo=='DSATUR' else 5, linewidth=2, capsize=4,
                    label=f'{algo}', alpha=0.8)
        
        # Plot theoretical data if available
        skip_algos_theo = ["QAOA (power)", 'QAOA_sim_total', 'QAOA_sim_avg', 'SAT', 'MCS', 'DSATUR', 'LMXRLF','qaoa_sim1_total','qaoa_sim1_avg']
        if algo not in skip_algos_theo:
            algo_theoretical = df_theoretical[df_theoretical['Algorithm'] == algo].sort_values('Nodes')
            if len(algo_theoretical) > 0:
                ax2.plot(algo_theoretical['Nodes'], algo_theoretical['TheoreticalTime'],
                        color=color, linestyle='--', linewidth=2, alpha=0.8,
                        label=f'{algo} (proj.exp)')

    ax2.set_xlabel('Number of Nodes', fontsize=16)
    ax2.set_ylabel('Time (log ms)', fontsize=14)
    ax2.set_yscale('log')
    ax2.tick_params(axis='both', which='major', labelsize=14)
    # ax1.set_title('Algorithm Performance Comparison', fontsize=12, fontweight='bold')
    ax2.text(0.02, 0.95, '(b)', transform=ax2.transAxes, fontsize=18, 
            fontweight='bold', verticalalignment='top')
    
    qaoa_data = df_actual[df_actual['Algorithm'] == 'QAOA'].sort_values('Nodes')
    if len(qaoa_data) >= 2:
        print(qaoa_data)
        x = qaoa_data['Nodes'].values
        y = qaoa_data['AverageTime'].values
        # Fit log10(y) = a*x + b
        logy = np.log10(y)
        a, b = np.polyfit(x, logy, 1)

        # Project up to 60 nodes
        x_proj = np.arange(x.min(), 61)  # or 51 if you want up to 51
        y_proj = 10**(a * x_proj + b)

        # Define the model: y = c * n^5
        def n5_model(n, c):
            return (c * n**2)

        # Fit the model to your data
        popt, _ = curve_fit(n5_model, x, y)
        c_fit = popt[0]

        # Project up to 61 nodes
        x_proj1 = np.arange(x.min(), 101)
        y_proj_n5 = n5_model(x_proj1, c_fit)

        def n5_model(n, c):
            k = np.log(n)
            return (c * (np.log(n)+np.log(2*k)))
#        Fit the model to your data
        popt, _ = curve_fit(n5_model, x, y)
        c_fit = popt[0]

        # Project up to 61 nodes
        x_proj2 = np.arange(x.min(), 101)
        y_proj_n6 = n5_model(x_proj1, c_fit)

        # Plot actual data and projection
        # ax1.plot(x_proj, y_proj, color='#1f77b4', linestyle='--', linewidth=2, 
        #         label=r'QAOA (proj.exp)')
        
        # ax1.plot(x_proj1, y_proj_n5, color="#9a0e8e", linestyle='--', linewidth=2, 
        #         label=r'QAOA (proj.quadratic)')
        
        ax2.plot(x_proj2, y_proj_n5, color="#6f22c7", linestyle='--', linewidth=2, 
                label=r'QAOA(proj)')
    ax2.legend(loc='lower right', fontsize=12,ncol=2)


    # Plot 3 (Bottom Left): QAOA Simulation Comparison
    qaoa_algorithms = ['QAOA', 'QAOA_sim_total', 'QAOA_sim_avg','qaoa_sim1_total']

    for algo in qaoa_algorithms:
        algo_data = df_actual[df_actual['Algorithm'] == algo].sort_values('Nodes')
        if len(algo_data) == 0:
            continue
        color = colors.get(algo, '#1f77b4')

        # For the special case you want: qaoa_sim1_total
        if algo=='QAOA':
            # Merge mean and CI: single errorbar
            ax3.errorbar(
                algo_data['Nodes'],
                algo_data['AverageTime'],
                yerr=[algo_data['CI_minus'], algo_data['CI_plus']],
                fmt='-o',                  # Line and markers
                color=color,
                markersize=6,
                linewidth=2,
                capsize=4,
                label=f'{algo}_real',
                alpha=0.8
            )
        else:
            if algo=='QAOA' or algo=='QAOA_sim_total':
                continue
            # For other QAOA sims: only the line, no errorbar
            if algo=='qaoa_sim1_total':
                algo1 = 'QAOA_sim'
                color = colors.get(algo, "#0a833a")
            elif algo =='QAOA_sim_avg':
                
                # algo1= 'QAOA_sim_1iter'
                continue
            
            ax3.plot(
                algo_data['Nodes'],
                algo_data['AverageTime'],
                color=color,
                linestyle='-',
                marker='o',
                markersize=6,
                linewidth=2,
                label=f'{algo1}',
                alpha=0.8
            )

    ax3.set_xlabel('Number of Nodes', fontsize=16)
    ax3.set_ylabel('Time (log ms)', fontsize=14)
    ax3.set_yscale('log')
    ax3.legend(loc='lower right', fontsize=12)
    ax3.tick_params(axis='both', which='major', labelsize=14)
    ax3.text(0.02, 0.95, '(c)', transform=ax3.transAxes, fontsize=18, fontweight='bold', verticalalignment='top')

    # Plot 4 (Bottom Right): Theoretical Complexity Projections
    theoretical_algorithms = df_theoretical['Algorithm'].unique()
    skip_algos_theo_plot = ['QAOA linear','QAOA_sim_total', 'QAOA_sim_avg','qaoa_sim1_total', 'qaoa_sim1_avg']

    for algo in theoretical_algorithms:
        if algo in skip_algos_theo_plot:
            continue
            
        algo_data = df_theoretical[df_theoretical['Algorithm'] == algo].sort_values('Nodes')
        if len(algo_data) == 0:
            continue
        color = colors.get(algo, '#1f77b4')
        if algo=='QAOA theo':
            algo='QAOA(proj)'
        ax1.plot(algo_data['Nodes'], algo_data['TheoreticalTime'],
                color=color, linestyle='--', linewidth=2.5, alpha=0.8,
                label=f'{algo}')

    ax1.set_xlabel('Number of Nodes', fontsize=16)
    ax1.set_ylabel('Time Complexity (log)', fontsize=14)
    ax1.set_yscale('log')
    ax1.legend(loc='upper left', fontsize=12, bbox_to_anchor=(0.07, 1))
    ax1.tick_params(axis='both', which='major', labelsize=14)
    # ax4.set_title('Theoretical Complexity Projections', fontsize=12, fontweight='bold')
    ax1.text(0.02, 0.95, '(a)', transform=ax1.transAxes, fontsize=18, 
            fontweight='bold', verticalalignment='top')

    # Apply consistent styling to all subplots
    for ax in [ax1, ax2, ax3]:
        ax.grid(True, alpha=0.3, linewidth=0.5)
        ax.set_axisbelow(True)
        
        # Style the spines
        for spine in ax.spines.values():
            spine.set_linewidth(1.0)
            spine.set_color('black')
            spine.set_alpha(0.8)

    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.20)
    plt.show()

    # # Save the figure
    # # plt.savefig('combined_algorithm_analysis.png', dpi=300, bbox_inches='tight', 
    # #             facecolor='white', edgecolor='none')
    # # plt.savefig('combined_algorithm_analysis.pdf', bbox_inches='tight', 
    # #             facecolor='white', edgecolor='none')

    # plt.show()
if __name__=='__main__':
    main()