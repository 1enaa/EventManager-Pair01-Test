def has_available_capacity(current_count, max_capacity):
    return current_count < max_capacity


def check_duplicate_registration(registered_ids, new_id):
    if new_id in registered_ids:
        raise ValueError(f"Participant {new_id} is already registered")
