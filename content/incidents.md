+++
title = "Incidents"
description = "Four real exploits replayed from their own transactions, on the deployed arithmetic and on exact, FP127 and FP19 arithmetic."
path = "results/incidents"

[extra]
group = "results"
+++

Each replay takes the attack's integers from the chain and runs the decisive calls again on several rulers: the deployed arithmetic, a fix in the same format, FP127, FP19 and exact rationals. It also says when a better ruler would not have helped. Balancer V1 is a rounding-direction case, not a precision one.

{{ <incidents /> }}
