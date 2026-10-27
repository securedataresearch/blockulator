+++
title = "Normal CDF"
description = "Every on-chain normal CDF we could measure, at the same exact points, against 150-digit arithmetic."
template = "cdf.html"
path = "results/cdf"

[extra]
group = "results"
+++

Option pricing and Gaussian bonding curves need Φ(x), the normal distribution's cumulative function, and on chain it is always an approximation. Each library here runs its own code at the same 385 points from −6 to 6, chosen so every format holds them exactly, and the result is compared with the exact value.

FP19 keeps 71 digits at every point. FP127 keeps 38 across the middle; in the far tail Φ(x) is near 10<sup>−9</sup>, and FP127's fixed 2<sup>−128</sup> grid leaves it 30 digits there. Lyra v1's options market uses Hart's rational approximation and keeps 16 digits, more than any price needs. solstat, Primitive's Gaussian library, states a maximum error of 1.2 × 10<sup>−7</sup> and meets it: about 7 digits, at a third of FP127's gas.

Primitive's earlier RMM-01 keeps about 2. Its `getCDF` uses the constant √2 in two places: once to scale x, which is right, and once as the Abramowitz and Stegun coefficient a<sub>3</sub>, where 1.421413741 belongs. Its error reaches 3.6 × 10<sup>−3</sup>, above the 3.15 × 10<sup>−3</sup> its own comment states. That is a wrong constant, not a limit of the number format: with the right one the same code is good to about 10<sup>−7</sup>. Primitive's later Portfolio uses solstat.

Lyra's CDF is a public library function, so its gas includes the call into the library, as it does where Lyra is deployed.
