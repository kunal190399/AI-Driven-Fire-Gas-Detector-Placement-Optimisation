# Model assumptions and limitations

This repository is an early-stage, transparent numerical prototype.

- The facility is a 2D horizontal plane; elevations and 3D obstructions are omitted.
- Dispersion is represented by a steady-state, reflected Gaussian plume approximation. It is not CFD and does not model transient releases, buoyancy, turbulence in complex structures, ventilation networks or thermal effects.
- Concentration is normalised per scenario. It is dimensionless and must not be interpreted as ppm, LFL fraction or a calibrated sensor reading.
- Obstacle handling attenuates grid values and uses a 2D segment/rectangle visibility check. It is not a validated flow or optical propagation model.
- Detector response uses a simple distance attenuation and local concentration proxy. It omits vendor-specific response curves, sensor technology, response time, poisoning, calibration drift and maintenance.
- The evolutionary algorithm is a compact Pareto-search demonstration. It does not guarantee a global optimum.

Any real deployment would require validated physics, site-specific geometry and meteorology, detector datasheets, applicable standards, formal engineering review and independent validation.
