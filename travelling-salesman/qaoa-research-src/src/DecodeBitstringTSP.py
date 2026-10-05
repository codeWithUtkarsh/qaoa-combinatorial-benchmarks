def generate_city_sequences(input_list, num_nodes):
    def backtrack(position, current_path):
        if position == len(input_list):
            # Fill in any missing nodes
            used_nodes = set(current_path)
            missing_nodes = [i for i in range(num_nodes) if i not in used_nodes]
            return [current_path + sorted(missing_nodes)]

        results = []
        choices = input_list[position]

        # Convert single integer to list for uniform processing
        if isinstance(choices, int):
            choices = [choices]

        # Find valid choices (not already used)
        used_nodes = set(current_path)
        valid_choices = [choice for choice in choices if choice not in used_nodes]

        # If no valid choices from original list, use all remaining nodes
        if not valid_choices and choices:
            # Check if any original choices were already used
            if any(choice in used_nodes for choice in choices):
                remaining_nodes = [i for i in range(num_nodes) if i not in used_nodes]
                valid_choices = remaining_nodes

        # If still no valid choices, terminate this path and fill missing
        if not valid_choices:
            missing_nodes = [i for i in range(num_nodes) if i not in used_nodes]
            return [current_path + sorted(missing_nodes)]

        # Explore each valid choice
        for choice in valid_choices:
            if choice not in current_path:  # Extra safety check
                results.extend(backtrack(position + 1, current_path + [choice]))

        return results

    return backtrack(0, [])