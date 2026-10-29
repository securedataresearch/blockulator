+++
title = "Incidents"
description = "Five real exploits replayed from their own transactions, on the deployed arithmetic and on exact, BL127 and BL19 arithmetic."
path = "results/incidents"

[extra]
group = "results"
+++

Each replay takes the attack's integers from the chain and runs the decisive calls again on several rulers: the deployed arithmetic, a fix in the same format, BL127, BL19 and exact rationals. It also says when a better ruler would not have helped. Balancer V1 is a rounding-direction case, not a precision one.

{{ <incidents /> }}
