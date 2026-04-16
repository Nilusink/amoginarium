"""
benchmark_plot.py
"""
import pandas as pd
import matplotlib.pyplot as plt

def generate_plot():
    try:
        df = pd.read_csv("collision_benchmarks.csv")
    except FileNotFoundError:
        print("Error: collision_benchmarks.csv not found. Run benchmark_collect.py first.")
        return

    plt.figure(figsize=(12, 8))

    # Extract N for the X-axis
    n_values = df["N"]

    # Plot each column except 'N'
    for column in df.columns:
        if column == "N":
            continue

        plt.plot(n_values, df[column], label=column, marker='.', markersize=4, alpha=0.8)

    # Apply logarithmic scaling to visualize the 10x steps properly
    plt.xscale('log')
    plt.yscale('log')

    plt.title("Collision Performance: Stack vs Heap vs Parallel", fontsize=14)
    plt.xlabel("Number of Entities (N)", fontsize=12)
    plt.ylabel("Avg Execution Time (ms) - Log Scale", fontsize=12)

    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))

    # Identify the theoretical crossover where N^2 dominates overhead
    plt.tight_layout()

    save_path = "collision_graph.png"
    plt.savefig(save_path, dpi=300)
    print(f"Graph saved as {save_path}")
    plt.show()

if __name__ == "__main__":
    generate_plot()