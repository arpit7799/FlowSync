from pathlib import Path
import math
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
ROUTES_DIR = BASE / "routes"
SCENARIO_DIR = BASE / "scenarios"

VEHICLE_TYPES = ROUTES_DIR / "vehicle_types.rou.xml"

ROUTES = {
    "north_to_south": "N_J1 J1_J2 J2_S",
    "south_to_north": "S_J2 J2_J1 J1_N",
    "west_to_east": "W_J3 J3_J4 J4_E",
    "east_to_west": "E_J4 J4_J3 J3_W",
    "north_to_west": "N_J1 J1_J3 J3_W",
    "north_to_east": "N_J1 J1_J2 J2_J4 J4_E",
    "south_to_west": "S_J2 J2_J4 J4_J3 J3_W",
    "south_to_east": "S_J2 J2_J4 J4_E",
    "west_to_north": "W_J3 J3_J1 J1_N",
    "east_to_south": "E_J4 J4_J2 J2_S",
}

DEMAND = {
    "low": 0.5,
    "medium": 1.5,
    "heavy": 3.0,
}

DURATION = 600


def select_vehicle_type(index: int, total: int) -> str:
    position = min(99, int(index * 100 / total))

    if position < 65:
        return "car"
    if position < 85:
        return "motorcycle"
    if position < 93:
        return "bus"
    return "truck"


def generate_scenario(name: str, rate: float) -> None:
    root = ET.Element("routes")

    vehicle_root = ET.parse(VEHICLE_TYPES).getroot()
    for vtype in vehicle_root.findall("vType"):
        root.append(vtype)

    for route_id, edges in ROUTES.items():
        ET.SubElement(root, "route", id=route_id, edges=edges)

    interval = 60.0 / rate
    vehicles_per_route = math.ceil(DURATION / interval)
    total_expected = vehicles_per_route * len(ROUTES)

    vehicles = []
    index = 0

    for route_id in ROUTES:
        departure = 0.0

        while departure < DURATION:
            vehicles.append({
                "id": f"{name}_{index:05d}",
                "type": select_vehicle_type(index, total_expected),
                "route": route_id,
                "depart": departure,
            })

            index += 1
            departure += interval

    # SUMO requires globally nondecreasing departure times.
    vehicles.sort(key=lambda vehicle: (vehicle["depart"], vehicle["id"]))

    for vehicle in vehicles:
        ET.SubElement(
            root,
            "vehicle",
            id=vehicle["id"],
            type=vehicle["type"],
            route=vehicle["route"],
            depart=f"{vehicle['depart']:.2f}",
            departLane="best",
            departSpeed="desired",
        )

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")

    output = SCENARIO_DIR / f"{name}.rou.xml"
    tree.write(output, encoding="UTF-8", xml_declaration=True)

    print(f"{name}: {len(vehicles)} vehicles generated and sorted")


def generate_emergency_scenario() -> None:
    root = ET.Element("routes")

    vehicle_root = ET.parse(VEHICLE_TYPES).getroot()
    for vtype in vehicle_root.findall("vType"):
        root.append(vtype)

    for route_id, edges in ROUTES.items():
        ET.SubElement(root, "route", id=route_id, edges=edges)

    # Base background traffic using low rate (0.5 veh/min)
    rate = DEMAND["low"]
    interval = 60.0 / rate
    vehicles_per_route = math.ceil(DURATION / interval)
    total_expected = vehicles_per_route * len(ROUTES)

    vehicles = []
    index = 0

    for route_id in ROUTES:
        departure = 0.0
        while departure < DURATION:
            vehicles.append({
                "id": f"emg_bg_{index:05d}",
                "type": select_vehicle_type(index, total_expected),
                "route": route_id,
                "depart": departure,
            })
            index += 1
            departure += interval

    # Add dedicated ambulances
    vehicles.append({
        "id": "ambulance_01",
        "type": "ambulance",
        "route": "north_to_south",
        "depart": 75.0,
    })
    vehicles.append({
        "id": "ambulance_02",
        "type": "ambulance",
        "route": "west_to_east",
        "depart": 220.0,
    })

    # Sort globally by departure time
    vehicles.sort(key=lambda vehicle: (vehicle["depart"], vehicle["id"]))

    for vehicle in vehicles:
        ET.SubElement(
            root,
            "vehicle",
            id=vehicle["id"],
            type=vehicle["type"],
            route=vehicle["route"],
            depart=f"{vehicle['depart']:.2f}",
            departLane="best",
            departSpeed="desired",
        )

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")

    output = SCENARIO_DIR / "emergency.rou.xml"
    tree.write(output, encoding="UTF-8", xml_declaration=True)
    print(f"emergency: {len(vehicles)} vehicles (including ambulances) generated and sorted")


if __name__ == "__main__":
    SCENARIO_DIR.mkdir(parents=True, exist_ok=True)

    for scenario, rate in DEMAND.items():
        generate_scenario(scenario, rate)

    generate_emergency_scenario()
