import typing as t
from argparse import ArgumentParser
from itertools import groupby
from collections import defaultdict
import logging

from pydantic import ValidationError

from scheduler import Scheduler
from event import Event


def print_schedule(schedule: Scheduler.Schedule):
    """Pretty prints the schedule."""
    for date, events in schedule.items():
        print(f'\n{date}')
        for event in events:
            print(f'\t{event}')


def get_field_errors(error: ValidationError):
    """Gets the unique exception types per data model field."""
    def error_wrapper_key(error_wrapper): return error_wrapper._loc
    error_wrappers = list(error.raw_errors)
    error_wrappers.sort(key=error_wrapper_key)

    field_errors: t.DefaultDict[str, t.Set[t.Type[Event.Error]]] = defaultdict(set)
    for name, errors in groupby(error_wrappers, key=error_wrapper_key):
        field_errors[name] = {type(error.exc) for error in errors}
    return field_errors


if __name__ == '__main__':
    logging.basicConfig(format='%(name)s: %(message)s')

    arg_parser = ArgumentParser()
    arg_parser.add_argument(
        '--input-events',
        action='store_true',
        help=(
            'Input one event per line in the format: "<start_date> -> <end_date> - <event_name>"'
            ' where: <start_date>, <end_date>: YYYY/MM/DD HH:mm'
            ' and <event_name>: Any valid character including spaces'
        )
    )

    known_args, unknown_args = arg_parser.parse_known_args()
    if known_args.input_events:
        scheduler = Scheduler()
        print('Enter blank line to stop event collection.')
        while True:
            # Input event string. Stop if blank line.
            event_str = input('New Event: ').strip()
            if not event_str:
                break
            try:
                # Extract event fields from string.
                event_fields = Event.fields_from_str(event_str)
                try:
                    # Create event using fields.
                    event = Event(**event_fields)
                    rescheduled = scheduler.schedule_event(event)
                    print(('Rescheduled' if rescheduled else 'Scheduled') + ' Event:', event)
                except ValidationError as error:
                    logging.error(error)
                    field_errors = get_field_errors(error)
                    # Reschedule event if set on invalid weekday or time.
                    if Event.TimeDeltaTooLargeError not in field_errors['__root__'] and (
                        Event.InvalidWeekDayError in field_errors['start']
                        or Event.InvalidWeekDayError in field_errors['end']
                        or Event.InvalidTimeError in field_errors['start']
                        or Event.InvalidTimeError in field_errors['end']
                    ):
                        # Reschedule event if datetimes are invalid.
                        event = scheduler.reschedule_invalid_event(**event_fields)
                        print('Rescheduled Event:', event)
                except Exception as ex:
                    logging.error('Unknown error. Skipping this event.')
                    break
            except Event.Error as error:
                logging.error(error)
            except Exception as ex:
                logging.error('Unknown error. Stopping event collection.')
                break

        print_schedule(scheduler.schedule)
