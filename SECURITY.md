# Security

Report a vulnerability in FP127, FP19, the ladder contracts or the site to
**sam@securedataresearch.net**, with "blockulator security" in the subject.
Please do not open a public issue for it.

Useful in a report: the op and the input (as the raw `int256` word), the result
you got, the result you expected, and how you computed the expected one. Every
op has an mpmath oracle (`scripts/fp127/oracle.py`, `scripts/fp19/oracle.py`),
so a precision report can be checked against it directly.

A fix ships as a new release at a new CREATE2
address (the contracts hold no state and have no owner, so nothing is paused or
upgraded in place), and the reporter is credited in `CHANGELOG.md` unless
they ask not to be.

Machine-readable contact: https://blockulator.com/.well-known/security.txt
