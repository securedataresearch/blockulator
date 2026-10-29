# Self-hosted third-party scripts

The site's third-party scripts, served from blockulator.com so no page loads code
from a CDN. Each file is copied unchanged from its package's npm registry tarball;
the tarball was checked against the registry's `dist.integrity` (sha512) before
anything was copied. Each directory keeps the package's own licence file. Fetched
2026-10-28.

| directory | files | used by | tarball | `dist.integrity` | licence |
|---|---|---|---|---|---|
| `katex@0.16.11/` | `dist/katex.min.css`, `dist/katex.min.js`, `dist/contrib/auto-render.min.js`, `dist/fonts/*` (the CSS names its fonts by relative path, so the layout is kept) | `templates/base.html`, on pages with `extra.math` | https://registry.npmjs.org/katex/-/katex-0.16.11.tgz | `sha512-RQrI8rlHY92OLf3rho/Ts8i/XvjgguEjOkO1BEXcU3N8BqPpSzBNwV/G0Ukr+P/l3ivvJUE/Fa/CwbS6HesGNQ==` | MIT (`LICENSE`) |
| `ethers@5.7.2/` | `dist/ethers.umd.min.js` | `templates/archive.html`, `templates/badges.html` | https://registry.npmjs.org/ethers/-/ethers-5.7.2.tgz | `sha512-wswUsmWo1aOK8rR7DIKiWSw9DbLWe6x98Jrn8wcTflTVvaXhAMaB5zGAXy0GYQEQp9iO1iSHWVyARQm11zUtyg==` | MIT (`LICENSE.md`) |
| `chart.js@4.4.0/` | `dist/chart.umd.js` (minified as published; it bundles `@kurkle/color` v0.3.2, MIT) | `static/js/islands/archive.js` (the archived futures app) | https://registry.npmjs.org/chart.js/-/chart.js-4.4.0.tgz | `sha512-vQEj6d+z0dcsKLlQvbKIMYFHd3t8W/7L2vfJIbYcfyPcRx92CsHqECpueN8qVGNlKyDcr5wBrYAYKnfu/9Q1hQ==` | MIT (`LICENSE.md`) |
| `@observablehq/plot@0.6.16/` | `dist/plot.umd.min.js` (expects the global `d3`) | `static/js/islands/plots.js` | https://registry.npmjs.org/@observablehq/plot/-/plot-0.6.16.tgz | `sha512-LRi9Rn93yUx90MIo2Md7+vazxO3Wiat14but2ttCER0xVS+jnfoUjuCGoz6H7bz/lgI9CFcW0HWlvWjMFjAv8g==` | ISC (`LICENSE`) |
| `d3@7.9.0/` | `dist/d3.min.js` (the version Plot 0.6.16 asks for, `^7.9.0`) | `static/js/islands/plots.js`, before Plot | https://registry.npmjs.org/d3/-/d3-7.9.0.tgz | `sha512-e1U46jVP+w7Iut8Jt8ri1YsPOvFpg46k+K8TpCb0P+zjCkjkPnV7WzfDJzMHy1LnA+wj5pLT1wjO901gLXeEhA==` | ISC (`LICENSE`) |

To check a copy, fetch the tarball, compare
`sha512-$(openssl dgst -sha512 -binary <tarball> | base64 -w0)` with the
integrity above, and diff the file against the one under `package/` in the
tarball. To update one, add a new `<name>@<version>/` directory the same way,
repoint the file that uses it, record it here, and delete the old directory.
