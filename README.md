# event-scheduler

Developed by Stefan Kairinos

This repo is my solution to the task described in task_description.pdf.  

Note: This was developed using VSCode. Some ease-of-use settings are pre-configured in the .vscode directory.

## How to setup

1. Create a virtual environment (venv) in the root directory;
2. Activate your venv;
3. Upgrade to the latest version of pip;
4. Pip install the requirements.txt;
5. (optional) Pip install the requirements.local.txt for linting and formatting support.

## How to run

1. Run command (make sure your venv is activated!): `python main.py --input-events`;
2. Enter event in the format specified in the task description. Repeat until satisfied.
3. Enter blank line to stop event collection.

Sample run:

```txt
Enter blank line to stop event collection.
New Event: 2022/08/23 15:00 -> 2022/08/23 16:00 - Meet Jamie for coffee
Scheduled Event: 2022/08/23 15:00 -> 2022/08/23 16:00 - Meet Jamie for coffee
New Event: 2022/08/23 16:15 -> 2022/08/23 17:00 - Guitar lessons
Scheduled Event: 2022/08/23 16:15 -> 2022/08/23 17:00 - Guitar lessons
New Event: 2022/11/12 09:00 -> 2022/11/12 10:00 - Dance party   
root: 2 validation errors for Event
start
  InvalidWeekDayError: Dates must be between Monday and Friday (type=value_error.invalidweekday)
end
  InvalidWeekDayError: Dates must be between Monday and Friday (type=value_error.invalidweekday)
Rescheduled Event: 2022/11/14 09:00 -> 2022/11/14 10:00 - Dance party
New Event: 

2022-08-23
        2022/08/23 15:00 -> 2022/08/23 16:00 - Meet Jamie for coffee
        2022/08/23 16:15 -> 2022/08/23 17:00 - Guitar lessons

2022-11-14
        2022/11/14 09:00 -> 2022/11/14 10:00 - Dance party
```

## Things to Note

- If error(s) occurs, a human readable description will be printed.

```txt
root: 2 validation errors for Event
start
  InvalidWeekDayError: Dates must be between Monday and Friday (type=value_error.invalidweekday)
end
  InvalidWeekDayError: Dates must be between Monday and Friday (type=value_error.invalidweekday)
```

- An event's scheduled start and end time are printed after each entry.

```txt
Scheduled Event: 2022/08/23 15:00 -> 2022/08/23 16:00 - Meet Jamie for coffee
```

- If an event is rescheduled, it will be stated.

```txt
Rescheduled Event: 2022/11/14 09:00 -> 2022/11/14 10:00 - Dance party
```

- The complete schedule will be printed once all events are collected.

```txt
2022-08-23
        2022/08/23 15:00 -> 2022/08/23 16:00 - Meet Jamie for coffee
        2022/08/23 16:15 -> 2022/08/23 17:00 - Guitar lessons

2022-11-14
        2022/11/14 09:00 -> 2022/11/14 10:00 - Dance party
```

## Unit Tests

To run unit tests simply run: `python -m unittest`. Alternatively, use VSCode's (or IDE of choice) built in test runner.  
Note: There's a known issue where 1 UT fails when run in parallel with the other UTs. However, if you run it independently, it passes.

This solution has high test coverage so it's recommended to review the UTs to better understand how this solution is intended to work.
