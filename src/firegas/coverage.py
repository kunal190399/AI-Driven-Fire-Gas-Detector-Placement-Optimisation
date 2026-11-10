"""Spatial detector response, obstacle line-of-sight and risk-weighted scoring."""
from __future__ import annotations
import numpy as np
from numpy.typing import NDArray
from .dispersion import all_concentrations, grid_for
from .facility import Facility, Obstacle
FloatArray = NDArray[np.float64]

def _segment_intersects_rect(a: tuple[float,float], b: tuple[float,float], r: Obstacle) -> bool:
    """Liang-Barsky segment/axis-aligned rectangle intersection."""
    x0,y0=a; x1,y1=b; dx,dy=x1-x0,y1-y0
    p=(-dx,dx,-dy,dy); q=(x0-r.x_min,r.x_max-x0,y0-r.y_min,r.y_max-y0)
    lo,hi=0.0,1.0
    for pi,qi in zip(p,q):
        if abs(pi)<1e-12:
            if qi<0: return False
            continue
        t=qi/pi
        if pi<0: lo=max(lo,t)
        else: hi=min(hi,t)
        if lo>hi: return False
    return True

def _visible(facility: Facility, a: tuple[float,float], b: tuple[float,float]) -> bool:
    return not any(_segment_intersects_rect(a,b,o) for o in facility.obstacles)

def evaluate_layout(facility: Facility, selected: tuple[int,...] | list[int],
                    threshold: float=.25, unit_cost: float=1.0,
                    detection_radius: float=18.0):
    """Return cost, mean/worst uncovered risk and scenario coverage masks.

    The response proxy is local relative concentration multiplied by exponential
    distance attenuation from each detector. Obstacle-intersecting cell-to-detector
    paths are excluded. It is illustrative, not a detector datasheet model.
    """
    if not selected: raise ValueError("A layout must contain at least one detector.")
    if detection_radius <= 0: raise ValueError("detection_radius must be positive.")
    detectors=[facility.candidate_points[i] for i in selected]
    fields=all_concentrations(facility); xx,yy=grid_for(facility)
    masks=[]; uncovered=[]
    for scenario,field in zip(facility.scenarios,fields):
        risk=np.maximum(field-threshold,0.0)*scenario.risk_weight
        response=np.zeros_like(field)
        for dx,dy in detectors:
            distance=np.hypot(xx-dx,yy-dy)
            visible=np.ones_like(field,dtype=bool)
            # Check visibility on the grid at a coarser stride for runtime; cells
            # between checked points use the same local visibility approximation.
            stride=max(1,int(round(2.0/facility.resolution)))
            for iy in range(0,field.shape[0],stride):
                for ix in range(0,field.shape[1],stride):
                    if not _visible(facility,(float(xx[iy,ix]),float(yy[iy,ix])),(dx,dy)):
                        y1=min(iy+stride,field.shape[0]); x1=min(ix+stride,field.shape[1])
                        visible[iy:y1,ix:x1]=False
            detector_response=field*np.exp(-distance/detection_radius)
            response=np.maximum(response,np.where(visible,detector_response,0.0))
        mask=response>=threshold; masks.append(mask)
        denom=float(risk.sum())
        uncovered.append(float((risk*(~mask)).sum()/denom) if denom>0 else 0.0)
    return len(selected)*unit_cost,float(np.mean(uncovered)),max(uncovered),masks
