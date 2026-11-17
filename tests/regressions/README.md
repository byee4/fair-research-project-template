# Regression tests for past agent (and human) mistakes

Rule: whenever you catch an agent mistake in review, add a failing test here
*before* fixing it, named `test_<YYYYMMDD>_<short_name>.py`, with a docstring that says
what went wrong, how it was caught, and the trace/session id. The suite then guards
every future session, regardless of which agent or model is used.
