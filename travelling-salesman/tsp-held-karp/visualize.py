import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv('./results/random_instance_res.csv')

print(data.columns)
# Create the figure and axis
plt.figure(figsize=(12, 8))

# Plot the data
plt.plot(data['Number of vertices'], data[' execution time [ns]'],
         marker='o', linestyle='-', linewidth=2, markersize=8)

# Add a title and labels
plt.title('Execution Time vs Number of Vertices', fontsize=18)
plt.xlabel('Number of Vertices', fontsize=14)
plt.ylabel('Execution Time (ns)', fontsize=14)

# Add grid for better readability
plt.grid(True, linestyle='--', alpha=0.7)

# Use logarithmic scale for y-axis as the execution time grows exponentially
plt.yscale('log')

# Add text annotation to highlight the exponential growth
plt.text(15, 1e6, 'Exponential Growth', fontsize=12)

# Customize tick parameters
plt.tick_params(axis='both', which='major', labelsize=12)

# Tight layout for better spacing
plt.tight_layout()

# Save the figure
plt.savefig('execution_time_graph.png', dpi=300)

# Show the plot
plt.show()