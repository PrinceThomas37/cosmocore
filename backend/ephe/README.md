# Swiss Ephemeris data files

Download ephemeris files (`.se1`) from:

https://www.astro.comftp/swisseph/ephe/

Or the GitHub mirror: https://github.com/aloistr/swisseph/tree/master/ephe

Place at least these files in this folder:

- `sepl_18.se1` (planets)
- `semo_18.se1` (moon)
- `seas_18.se1` (asteroids, optional for Chiron)

Without them, `pyswisseph` may fall back to Moshier with reduced accuracy.
