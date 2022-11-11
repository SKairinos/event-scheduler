from argparse import ArgumentParser
from itertools import groupby
import logging

from pydantic import ValidationError

from scheduler import Scheduler
from event import Event


def print_schedule(schedule: Scheduler.Schedule):
    for date, events in schedule.items():
        print(f'\n{date}')
        for event in events:
            print(f'\t{event}')


def get_field_errors(error: ValidationError):
    def error_wrapper_key(error_wrapper): return error_wrapper._loc
    error_wrappers = list(error.raw_errors)
    error_wrappers.sort(key=error_wrapper_key)
    return {
        name: [error.exc for error in errors]
        for name, errors in groupby(error_wrappers, key=error_wrapper_key)
    }


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
                    scheduler.schedule_event(event)
                    print('Scheduled Event:', event)
                except ValidationError as error:
                    logging.error(error)
                    field_errors = get_field_errors(error)

                    if 'start' in field_errors and all(
                        type(error) in [Event.InvalidDayError, Event.InvalidTimeError]
                        for error in field_errors['start']
                    ):
                        # Reschedule event if datetimes are invalid.
                        event = scheduler.reschedule_invalid_event(**event_fields)
                        print('Rescheduled Event:', event)

                except Exception as ex:
                    logging.error('Unknown error. Stopping event collection.')
                    break
            except Event.Error as error:
                logging.error(error)
            except Exception as ex:
                logging.error('Unknown error. Stopping event collection.')
                break

        print_schedule(scheduler.schedule)


# 2022/08/23 15:00 -> 2022/08/23 16:00 - Meet Jamie for coffee
# 2022/08/23 15:15 -> 2022/08/23 16:00 - Guitar lessons
# 2022/11/12 15:00 -> 2022/11/12 16:00 - Meet Jamie for coffee
