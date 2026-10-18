
def filter_events_by_location(events, location):
    """Filter events by location, ignoring letter case."""
    search_location = location.casefold()

    return [
        event
        for event in events
        if search_location in event["location"].casefold()
    ]


def filter_events_by_title(events, title):
    """Filter events by title, ignoring letter case."""
    search_title = title.casefold()

    return [
        event
        for event in events
        if search_title in event["title"].casefold()
    ]
