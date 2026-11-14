"""Emergency vehicle detection and route tracking for SUMO."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import traci


@dataclass
class TrackedEmergencyVehicle:
    vehicle_id: str
    vehicle_type: str
    current_edge: str
    lane_id: str
    position_m: float
    lane_length_m: float
    distance_to_stopline_m: float
    speed_mps: float
    route: List[str]
    route_index: int
    target_junction: Optional[str]
    next_edge: Optional[str]
    required_phase: Optional[int]


class EmergencyVehicleDetector:
    """Monitors SUMO simulation for emergency vehicles (ambulance, vClass=emergency)."""

    def __init__(self, emergency_types: Tuple[str, ...] = ("ambulance",)):
        self.emergency_types = set(emergency_types)
        # Cache junction incoming edges
        self.junction_approaches: Dict[str, Dict[str, str]] = {}  # incoming_edge -> junction_id

    def is_emergency_vehicle(self, vehicle_id: str) -> bool:
        """Check if vehicle is an emergency vehicle by type or vClass."""
        try:
            vtype = traci.vehicle.getTypeID(vehicle_id)
            if vtype in self.emergency_types:
                return True
            vclass = traci.vehicle.getVehicleClass(vehicle_id)
            if vclass == "emergency":
                return True
        except traci.TraCIException:
            return False
        return False

    def scan_for_emergency_vehicles(self, runtimes: dict) -> List[TrackedEmergencyVehicle]:
        """Scan simulation and extract state for all active emergency vehicles."""
        tracked = []
        try:
            vehicle_ids = traci.vehicle.getIDList()
        except traci.TraCIException:
            return []

        for vid in vehicle_ids:
            if not self.is_emergency_vehicle(vid):
                continue

            try:
                lane_id = traci.vehicle.getLaneID(vid)
                edge_id = traci.vehicle.getRoadID(vid)
                if not edge_id or edge_id.startswith(":"):
                    # Vehicle is inside an internal junction lane
                    continue

                pos = traci.vehicle.getLanePosition(vid)
                lane_len = traci.lane.getLength(lane_id)
                dist_to_stop = max(0.0, lane_len - pos)
                speed = traci.vehicle.getSpeed(vid)
                route = traci.vehicle.getRoute(vid)
                route_idx = traci.vehicle.getRouteIndex(vid)
                vtype = traci.vehicle.getTypeID(vid)

                next_edge = route[route_idx + 1] if route_idx >= 0 and route_idx + 1 < len(route) else None

                # Find which junction this edge leads to
                target_junction, req_phase = self._resolve_target_junction_and_phase(
                    edge_id, next_edge, runtimes
                )

                tracked.append(
                    TrackedEmergencyVehicle(
                        vehicle_id=vid,
                        vehicle_type=vtype,
                        current_edge=edge_id,
                        lane_id=lane_id,
                        position_m=round(pos, 2),
                        lane_length_m=round(lane_len, 2),
                        distance_to_stopline_m=round(dist_to_stop, 2),
                        speed_mps=round(speed, 2),
                        route=list(route),
                        route_index=route_idx,
                        target_junction=target_junction,
                        next_edge=next_edge,
                        required_phase=req_phase,
                    )
                )
            except traci.TraCIException:
                continue

        return tracked

    def _resolve_target_junction_and_phase(
        self,
        incoming_edge: str,
        next_edge: Optional[str],
        runtimes: dict,
    ) -> Tuple[Optional[str], Optional[int]]:
        """Determine target junction and required signal phase."""
        for junction_id, runtime in runtimes.items():
            try:
                links = traci.trafficlight.getControlledLinks(junction_id)
            except traci.TraCIException:
                continue

            for phase in (0, 2):
                phase_indices = runtime.phase_links.get(phase, []) + runtime.shared_links
                for link_idx in phase_indices:
                    if link_idx < len(links):
                        for conn in links[link_idx]:
                            in_lane, out_lane, _ = conn
                            in_edge = traci.lane.getEdgeID(in_lane)
                            out_edge = traci.lane.getEdgeID(out_lane)

                            if in_edge == incoming_edge:
                                if next_edge is None or out_edge == next_edge:
                                    return junction_id, phase

        return None, None
