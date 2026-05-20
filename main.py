from data.generator import generate_mdmkp_instance
from src.algorithms.alns.core import ALNSConfig
from src.algorithms.mdmkp.alns_solver import MDMKPALNSSolver
from src.algorithms.mdmkp.greedy import GreedyMDMKP


def main():
    # Tao instance: 50 vat pham, 3 balo, 3 chieu (weight, volume, energy)
    instance = generate_mdmkp_instance(
        n_items=50,
        n_knapsacks=3,
        n_dimensions=3,
        capacity_ratio=0.6,
        seed=42,
    )
    print(f"Instance: {instance}")
    print(f"  Items: {instance.n_items}, Knapsacks: {instance.n_knapsacks}, Dimensions: {instance.n_dimensions}")
    print()

    # --- Greedy ---
    greedy_solution = GreedyMDMKP(instance).solve()
    print(f"[Greedy]  {greedy_solution}")

    # --- ALNS ---
    config = ALNSConfig(max_iterations=5000, seed=42)
    result = MDMKPALNSSolver(instance, config).solve()
    print(f"[ALNS]    value={result.best_value:.2f}, time={result.runtime:.3f}s, iterations={result.iterations}")
    print(f"          {result.best_solution}")

    # So sanh
    if greedy_solution.total_value > 0:
        improvement = (result.best_value - greedy_solution.total_value) / greedy_solution.total_value * 100
        print(f"\nImprovement: {improvement:+.2f}% so voi Greedy")

    # Trong so operator cuoi cung
    print(f"\nDestroy weights: {result.destroy_weights}")
    print(f"Repair weights:  {result.repair_weights}")


if __name__ == "__main__":
    main()
