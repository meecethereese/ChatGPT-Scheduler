import sys
import os
import re
from collections import deque

class Process:
    def __init__(self, name, arrival, burst):
        self.name = name
        self.arrival = arrival
        self.burst = burst
        self.remaining_time = burst
        self.start_time = None
        self.end_time = None
        self.first_scheduled = False

    def __repr__(self):
        return f"Process(name={self.name}, arrival={self.arrival}, burst={self.burst})"


def parse_input(input_file):
    processes = []
    run_for = 0
    algorithm = ""
    quantum = None  # Initialize quantum with None by default

    with open(input_file, 'r') as f:
        for line in f:
            tokens = line.split()
            if tokens[0] == 'process':
                name = tokens[2]
                arrival = int(tokens[4])
                burst = int(tokens[6])
                processes.append(Process(name, arrival, burst))
            elif tokens[0] == 'runfor':
                run_for = int(tokens[1])
            elif tokens[0] == 'use':
                algorithm = tokens[1]
            elif tokens[0] == 'quantum':
                quantum = int(tokens[1])  # Set quantum only for Round-Robin

    # Sort processes by their arrival time upfront
    processes.sort(key=lambda p: p.arrival)

    return processes, run_for, algorithm, quantum

def fifo_scheduler(processes, run_for):
    timeline = []
    unfinished_processes = []
    current_time = 0
    ready_queue = deque()  # Queue to hold processes in arrival order
    i = 0  # Index to track processes
    running_process = None  # Track the currently running process

    while current_time < run_for:
        # 1. Log arrivals of processes that have arrived at the current time
        while i < len(processes) and processes[i].arrival <= current_time:
            timeline.append(f"Time {current_time:>4} : {processes[i].name} arrived")
            ready_queue.append(processes[i])
            i += 1

        # 2. Check if the running process has finished
        if running_process and running_process.remaining_time == 0:
            timeline.append(f"Time {current_time:>4} : {running_process.name} finished")
            running_process.end_time = current_time  # Set the end time for metrics calculation
            running_process = None  # Process is done

        # 3. If there's no running process, select one from the ready queue
        if running_process is None and ready_queue:
            running_process = ready_queue.popleft()

            # Record the start time if it's the first time the process is being selected
            if running_process.start_time is None:
                running_process.start_time = current_time

            # Log the selection of the process
            timeline.append(f"Time {current_time:>4} : {running_process.name} selected (burst {running_process.remaining_time})")

        # 4. If no process is running and the queue is empty, log idle time
        if running_process is None and not ready_queue:
            timeline.append(f"Time {current_time:>4} : Idle")

        # 5. Increment the current time by 1
        current_time += 1

        # 6. Decrement the remaining time of the running process (after current_time is incremented)
        if running_process:
            running_process.remaining_time -= 1  # Decrease remaining time after time is incremented

    # 7. Check for unfinished processes
    for process in processes:
        if process.end_time is None or process.end_time > run_for:
            unfinished_processes.append(process.name)

    return timeline, unfinished_processes

def sjf_scheduler(processes, run_for):
    timeline = []
    unfinished_processes = []
    current_time = 0
    ready_queue = []
    processes.sort(key=lambda p: p.arrival)  # Sort by arrival time
    i = 0  # Index to track processes

    running_process = None  # Track the currently running process

    while current_time < run_for:
        # 1. Add processes that have arrived to the ready queue
        while i < len(processes) and processes[i].arrival <= current_time:
            timeline.append(f"Time {current_time:>4} : {processes[i].name} arrived")
            ready_queue.append(processes[i])
            i += 1

        # 2. Check if the current running process finishes and log it immediately after arrival logic
        if running_process and running_process.remaining_time == 0:
            running_process.end_time = current_time
            timeline.append(f"Time {current_time:>4} : {running_process.name} finished")
            running_process = None  # Process is done

        # 3. Sort the ready queue by remaining time (preemptive SJF behavior)
        ready_queue.sort(key=lambda p: p.remaining_time)

        # 4. If a new process arrives with a shorter burst time, preempt the current process
        if running_process and ready_queue and ready_queue[0].remaining_time < running_process.remaining_time:
            ready_queue.append(running_process)  # Put the preempted process back in the ready queue
            running_process = None

        # 5. If there's no running process, select one from the ready queue
        if running_process is None and ready_queue:
            running_process = ready_queue.pop(0)

            # Set the start time only once when the process is first selected
            if running_process.start_time is None:
                running_process.start_time = current_time  # Set the start time when first scheduled

            timeline.append(f"Time {current_time:>4} : {running_process.name} selected (burst {running_process.remaining_time})")

        # 6. If no process is running and no new arrivals, log idle time
        if running_process is None and not ready_queue and i >= len(processes):
            timeline.append(f"Time {current_time:>4} : Idle")

        # 7. Increment the current time (before decrementing remaining time)
        current_time += 1

        # 8. Decrement the remaining time of the running process (this happens after the current time is incremented)
        if running_process:
            running_process.remaining_time -= 1

    # 9. Check for any unfinished processes
    for process in processes:
        if process.remaining_time > 0:
            unfinished_processes.append(process.name)

    return timeline, unfinished_processes

def round_robin_scheduler(processes, run_for, quantum):
    timeline = []  # Should be a list of strings
    current_time = 0
    ready_queue = []
    process_index = 0  # Index to track the next arriving process
    running_process = None  # Keep track of the currently running process
    quantum_counter = 0  # Track how much of the quantum has been used

    while current_time < run_for:
        # 1. Check for new arrivals based on sorted process list
        while process_index < len(processes) and processes[process_index].arrival == current_time:
            process = processes[process_index]
            # Ensure that we are appending only strings
            timeline.append(f"Time {current_time:>4} : {process.name} arrived")
            ready_queue.append(process)
            process_index += 1

        # 2. Handle running process logic (check if process finishes or is preempted)
        if running_process:
            # If the process has finished, log it and stop running it
            if running_process.remaining_time == 0:
                timeline.append(f"Time {current_time:>4} : {running_process.name} finished")
                running_process.end_time = current_time
                running_process = None  # The process is done, no longer running

            # If the quantum is used up and the process is not finished, preempt it
            elif quantum_counter == quantum:
                ready_queue.append(running_process)
                running_process = None  # Preempt the process

        # 3. If no process is running, select the next process from the ready queue
        if running_process is None and ready_queue:
            running_process = ready_queue.pop(0)
            quantum_counter = 0  # Reset quantum counter for the new process

            # If the process is being scheduled for the first time, set its start time
            if running_process.start_time is None:
                running_process.start_time = current_time

            # Log the process selection (as a string)
            timeline.append(f"Time {current_time:>4} : {running_process.name} selected (burst {running_process.remaining_time:>3})")

        # 4. If no process is running and no new arrivals, log idle time
        if running_process is None and not ready_queue:
            timeline.append(f"Time {current_time:>4} : Idle")

        # 5. Increment the current time by 1 (this happens at the end of the loop)
        current_time += 1

        # 6. Decrement the remaining time and increment the quantum counter after current_time is updated
        if running_process:
            running_process.remaining_time -= 1
            quantum_counter += 1

    # Ensure that any unfinished processes are marked with an end_time
    unfinished_processes = []
    for process in processes:
        if process.remaining_time > 0:
            process.end_time = run_for
            unfinished_processes.append(process.name)

    return timeline, unfinished_processes  # Ensure that timeline is a list of strings

def calculate_metrics(processes):
    metrics = []
    for process in processes:
        # Turnaround time = end_time - arrival time
        turnaround_time = process.end_time - process.arrival
        # Waiting time = turnaround_time - burst time
        waiting_time = turnaround_time - process.burst
        # Response time = start_time - arrival time (only the first time it is selected)
        response_time = process.start_time - process.arrival if process.start_time is not None else 0
        metrics.append((process.name, waiting_time, turnaround_time, response_time))
    return metrics

def write_output(file_name, processes, timeline, metrics, run_for, algorithm, quantum=None, unfinished_processes=None):
    def process_key(process_name):
        # Extract numeric part from process name (e.g., P1 -> 1)
        import re
        return int(re.search(r'\d+', process_name).group())

    with open(file_name, 'w') as f:
        # First, output the number of processes and the scheduling algorithm used
        f.write(f"{len(processes)} processes\n")

        if algorithm == 'rr':
            f.write("Using Round-Robin\n")
            f.write(f"Quantum   {quantum}\n")
        elif algorithm == 'fifo':
            f.write("Using First In, First Out\n")
        elif algorithm == 'fcfs':
            f.write("Using First-Come First-Served\n")
        elif algorithm == 'sjf':
            f.write("Using preemptive Shortest Job First\n")

        f.write("\n")  # Blank line before time ticks

        # Write the scheduling timeline with proper formatting
        for event in timeline:
            f.write(event + '\n')  # Ensure event is a string

        # Print "Finished at time X" followed by a newline, and then a blank line below
        f.write(f"Finished at time {run_for}\n\n")  # Two newlines to create a blank line below

        # Sort the metrics by process name (e.g., P1, P2, P3) by extracting the number from the name
        metrics_sorted = sorted(metrics, key=lambda x: process_key(x[0]))

        # Write the process metrics: waiting time, turnaround time, response time
        for metric in metrics_sorted:
            name, wait, turnaround, response = metric
            f.write(f"{name} wait   {wait} turnaround   {turnaround} response   {response}\n")

        # Check for unfinished processes and print them
        if unfinished_processes:
            unfinished_sorted = sorted(unfinished_processes, key=process_key)
            for process in unfinished_sorted:
                f.write(f"{process} did not finish\n")


def main():
    # Check if the correct number of arguments are provided
    if len(sys.argv) != 2:
        print("Usage: scheduler-gpt.py <input_file.in>")
        sys.exit(1)

    # Get the input file from the command-line argument
    input_file = sys.argv[1]

    # Ensure the input file has a .in extension
    if not input_file.endswith('.in'):
        print("Error: Input file must have a .in extension.")
        sys.exit(1)

    # Generate the output file name by replacing the .in extension with .out
    base_filename = os.path.splitext(input_file)[0]
    output_file = f"{base_filename}.out"

    # Process the input and execute the scheduling algorithm
    processes, run_for, algorithm, quantum = parse_input(input_file)

    # Treat both 'fifo' and 'fcfs' as First-Come First-Served and run the FIFO scheduler
    if algorithm == 'fifo' or algorithm == 'fcfs':
        timeline, unfinished_processes = fifo_scheduler(processes, run_for)
    elif algorithm == 'sjf':
        timeline, unfinished_processes = sjf_scheduler(processes, run_for)
    elif algorithm == 'rr':
        if quantum is None:
            print("Error: Quantum value is required for Round-Robin scheduling.")
            sys.exit(1)
        timeline, unfinished_processes = round_robin_scheduler(processes, run_for, quantum)

    # Calculate metrics for each process
    metrics = calculate_metrics(processes)

    # Write the output to the output file
    write_output(output_file, processes, timeline, metrics, run_for, algorithm, quantum, unfinished_processes)

if __name__ == "__main__":
    main()

