+++
title = "Normal CDF"
description = "Every on-chain normal CDF we could measure, at the same exact points, against 150-digit arithmetic."
template = "cdf.html"
path = "results/cdf"

[extra]
group = "results"
+++

Option pricing and Gaussian bonding curves need Φ(x), the normal distribution's cumulative function, and on chain it is always an approximation. Each library here runs its own code at the same 385 points from −6 to 6, chosen so every format holds them exactly, and the result is compared with the exact value.

FP19 keeps 71 digits at every point. FP127 keeps 38 across the middle; in the far tail Φ(x) is near 10<sup>−9</sup>, and FP127's fixed 2<sup>−128</sup> grid leaves it 30 digits there. solstat, Primitive's Gaussian library, states a maximum error of 1.2 × 10<sup>−7</sup> and meets it: about 7 digits, at a third of FP127's gas.
