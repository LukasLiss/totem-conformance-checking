"""
TOTeM Conformance Evaluation Script

Evaluates the runtime of the conformance algorithm across different event logs
and tau values. Results are saved to a CSV file incrementally, allowing the
script to be stopped and resumed.
"""

import os
import sys
import csv
import time
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from totem_lib import import_ocel, totemDiscovery, conformance_of_totem

# --- Configuration ---
EVALUATION_DATA_DIR = os.path.join(os.path.dirname(__file__), 'evaluation_data')
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), 'totem_conformance_eval_results.csv')
TAU_VALUES = [round(i * 0.1, 1) for i in range(11)]  # 0.0, 0.1, ..., 1.0
NUM_RUNS = 3
SUPPORTED_EXTENSIONS = ('.json', '.xml', '.sqlite', '.csv')

CSV_FIELDNAMES = [
    'file_name', 'tau', 'run_index',
    'num_events', 'num_objects', 'num_object_types', 'num_related_object_pairs',
    'num_totem_nodes', 'num_totem_arcs',
    'temporal_fitness', 'temporal_precision',
    'log_card_fitness', 'log_card_precision',
    'event_card_fitness', 'event_card_precision',
    'discovery_time_sec', 'conformance_time_sec',
]


def count_related_object_pairs(ocel):
    """Count unique object pairs connected via shared events (e2o) or o2o edges."""
    pairs = set()
    # e2o: object pairs sharing an event
    for row in ocel.events.iter_rows(named=True):
        objects = row["_objects"]
        if objects and len(objects) > 1:
            obj_list = sorted(set(objects))
            for i in range(len(obj_list)):
                for j in range(i + 1, len(obj_list)):
                    pairs.add((obj_list[i], obj_list[j]))
    # o2o: explicit object-to-object edges
    for src, tgt in ocel.o2o_graph_edges:
        pair = tuple(sorted((src, tgt)))
        pairs.add(pair)
    return len(pairs)


def compute_totem_arcs(totem):
    """Count total arcs in the tempgraph."""
    return (
        len(totem.tempgraph.get("D", set()))
        + len(totem.tempgraph.get("I", set()))
        + len(totem.tempgraph.get("P", set()))
    )


def load_completed_runs(csv_path):
    """Load already-completed (file_name, tau, run_index) from CSV."""
    completed = set()
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row['file_name'], float(row['tau']), int(row['run_index']))
                completed.add(key)
    return completed


def append_row(csv_path, row_dict):
    """Append a single row to CSV, writing header if file is new."""
    file_exists = os.path.exists(csv_path) and os.path.getsize(csv_path) > 0
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row_dict)


def get_log_files(data_dir):
    """Get sorted list of event log files with supported extensions."""
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(glob.glob(os.path.join(data_dir, f'*{ext}')))
    return sorted(files)


def main():
    completed = load_completed_runs(OUTPUT_CSV)
    log_files = get_log_files(EVALUATION_DATA_DIR)

    print(f"Found {len(log_files)} event log files")
    print(f"Already completed: {len(completed)} runs")
    print(f"Tau values: {TAU_VALUES}")
    print(f"Runs per configuration: {NUM_RUNS}")
    print(f"Output CSV: {OUTPUT_CSV}")

    for file_path in log_files:
        file_name = os.path.basename(file_path)
        print(f"\n{'='*60}")
        print(f"Processing: {file_name}")
        print(f"{'='*60}")

        # Check if all runs for this file are already done
        all_done = all(
            (file_name, tau, run_idx) in completed
            for tau in TAU_VALUES
            for run_idx in range(1, NUM_RUNS + 1)
        )
        if all_done:
            print(f"  All runs already completed, skipping file.")
            continue

        # Load the OCEL once per file
        try:
            print(f"  Loading OCEL...")
            ocel = import_ocel(file_path)
        except Exception as e:
            print(f"  ERROR loading {file_name}: {e}")
            continue

        # Compute log characteristics once per file
        num_events = ocel.events.height
        num_objects = ocel.objects.height
        num_object_types = len(ocel.object_types)
        print(f"  Computing related object pairs...")
        num_related_object_pairs = count_related_object_pairs(ocel)

        print(f"  Events: {num_events}, Objects: {num_objects}, "
              f"Types: {num_object_types}, Related pairs: {num_related_object_pairs}")

        for tau in TAU_VALUES:
            for run_idx in range(1, NUM_RUNS + 1):
                key = (file_name, tau, run_idx)
                if key in completed:
                    continue

                print(f"  tau={tau}, run={run_idx}/{NUM_RUNS} ... ", end="", flush=True)

                try:
                    # Time discovery
                    t0 = time.time()
                    totem = totemDiscovery(ocel, tau=tau)
                    discovery_time = time.time() - t0

                    # Time conformance
                    t0 = time.time()
                    conformance = conformance_of_totem(totem, ocel)
                    conformance_time = time.time() - t0

                    overall = conformance["overall_metrics"]

                    row = {
                        'file_name': file_name,
                        'tau': tau,
                        'run_index': run_idx,
                        'num_events': num_events,
                        'num_objects': num_objects,
                        'num_object_types': num_object_types,
                        'num_related_object_pairs': num_related_object_pairs,
                        'num_totem_nodes': len(totem.tempgraph.get("nodes", set())),
                        'num_totem_arcs': compute_totem_arcs(totem),
                        'temporal_fitness': overall['temporal']['fitness'],
                        'temporal_precision': overall['temporal']['precision'],
                        'log_card_fitness': overall['log_cardinality']['fitness'],
                        'log_card_precision': overall['log_cardinality']['precision'],
                        'event_card_fitness': overall['event_cardinality']['fitness'],
                        'event_card_precision': overall['event_cardinality']['precision'],
                        'discovery_time_sec': round(discovery_time, 4),
                        'conformance_time_sec': round(conformance_time, 4),
                    }

                    # Replace None with empty string for CSV
                    for k, v in row.items():
                        if v is None:
                            row[k] = ''

                    append_row(OUTPUT_CSV, row)
                    print(f"discovery={discovery_time:.2f}s, conformance={conformance_time:.2f}s")

                except Exception as e:
                    print(f"ERROR: {e}")
                    continue

    print(f"\nAll done. Results saved to {OUTPUT_CSV}")


if __name__ == '__main__':
    main()
