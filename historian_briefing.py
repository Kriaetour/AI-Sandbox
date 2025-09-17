import re
import json
import sys
import argparse
from collections import defaultdict

LOG_FILE = "log.txt"
TICKS_PER_ERA = 500  # Era block size (was 1000)

# Regex patterns for significant events
event_patterns = [
    # Faction founding (not present in sample, keep for future)
    (re.compile(r"Faction (?P<faction>[\w_ ]+) founded at tick=(?P<tick>\d+)", re.IGNORECASE), "FACTION_FOUNDED"),
    # Population milestone (birth event) - match log format
    (re.compile(r"Faction\.(?P<faction>[\w_]+)\s+\S+:\s*Birth event -> (?P<name>\w+)", re.IGNORECASE), "POPULATION_MILESTONE"),
    # Resource focus (not present in sample, keep for future)
    (re.compile(r"Faction (?P<faction>[\w_ ]+) focus resource: (?P<resource>\w+) at tick=(?P<tick>\d+)", re.IGNORECASE), "RESOURCE_FOCUS"),
    # Territory conflict (combat)
    (re.compile(r"Combat: (?P<attacker>[\w_]+) attacks (?P<defender>[\w_]+) for (?P<damage>\d+) damage", re.IGNORECASE), "TERRITORY_CONFLICT"),
    # Harvesting - match log format
    (re.compile(r"Faction\.(?P<faction>[\w_]+)\s+\S+ harvested.*?Food:(?P<food>[\d.]+)\s+Wood:(?P<wood>[\d.]+)\s+Ore:(?P<ore>[\d.]+)", re.IGNORECASE), "HARVEST_EVENT"),
    # NPC Deaths / Mortality
    (re.compile(r"Death event.*NPC (?P<npc>[\w_]+).*at tick=(?P<tick>\d+)"), "DEATH_EVENT"),
    # Starvation
    (re.compile(r"Starvation pressure.*Faction (?P<faction>[\w_ ]+).*lost (?P<count>\d+) members.*tick=(?P<tick>\d+)"), "STARVATION_EVENT"),
    # Diplomacy / Alliance
    (re.compile(r"Alliance formed between (?P<faction1>[\w_ ]+) and (?P<faction2>[\w_ ]+) at tick=(?P<tick>\d+)"), "ALLIANCE_FORMED"),
    (re.compile(r"Treaty signed between (?P<faction1>[\w_ ]+) and (?P<faction2>[\w_ ]+) at tick=(?P<tick>\d+)"), "TREATY_SIGNED"),
    # Weather / Environmental
    (re.compile(r"(?P<event>Blizzard|Drought|Flood|Storm) (begins|at) tick=(?P<tick>\d+)"), "WEATHER_EVENT"),
    # Technology / Culture
    (re.compile(r"Technology unlocked: (?P<tech>[\w_ ]+) at tick=(?P<tick>\d+)"), "TECH_UNLOCKED"),
    (re.compile(r"Cultural festival: (?P<festival>[\w_ ]+) at tick=(?P<tick>\d+)"), "CULTURE_EVENT"),
    (re.compile(r"Ritual completed: (?P<ritual>[\w_ ]+) at tick=(?P<tick>\d+)"), "RITUAL_COMPLETED"),
    # Resource Depletion / Discovery
    (re.compile(r"Resource node depleted: (?P<resource>[\w_ ]+) at \((?P<x>\d+), (?P<y>\d+)\) tick=(?P<tick>\d+)"), "RESOURCE_DEPLETED"),
    (re.compile(r"New resource discovered: (?P<resource>[\w_ ]+) at \((?P<x>\d+), (?P<y>\d+)\) tick=(?P<tick>\d+)"), "RESOURCE_DISCOVERED"),
    # Leadership Changes
    (re.compile(r"New leader for Faction (?P<faction>[\w_ ]+) at tick=(?P<tick>\d+)"), "LEADERSHIP_CHANGE"),
    # Social Events: Rumors and Sayings
    (re.compile(r"\[Rumors\] Created (\d+) new rumors at tick (\d+)", re.IGNORECASE), "RUMOR_EVENT"),
    (re.compile(r"\[Sayings\] Created (\d+) sayings at tick (\d+)", re.IGNORECASE), "SAYING_EVENT"),
]

def parse_tick_from_line(line, match=None, fallback_tick=None):
    # Try to extract tick from the log line (if present or from regex group)
    if match and "tick" in match.groupdict() and match.group("tick"):
        return int(match.group("tick"))
    m = re.search(r"tick=(\d+)", line)
    if m:
        return int(m.group(1))
    # Try to extract from timestamp if present (use as fallback, e.g. line number or None)
    if fallback_tick is not None:
        return fallback_tick
    return None

def parse_events(log_path):
    events = []
    unmatched_lines = 0
    matched_lines = 0
    with open(log_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            matched = False
            for pattern, event_type in event_patterns:
                m = pattern.search(line)
                if m:
                    matched = True
                    # Try to extract tick, fallback to line number if not found
                    tick = parse_tick_from_line(line, m, fallback_tick=line_num)
                    if not tick:
                        print(f"[DEBUG] Line {line_num}: Matched {event_type} but no tick found: {line.strip()}")
                        continue
                    event = {"tick": tick, "type": event_type}
                    if event_type == "FACTION_FOUNDED":
                        event["faction"] = m.group("faction").strip()
                    elif event_type == "POPULATION_MILESTONE":
                        event["faction"] = m.group("faction")
                        event["name"] = m.group("name")
                    elif event_type == "RESOURCE_FOCUS":
                        event["faction"] = m.group("faction").strip()
                        event["resource"] = m.group("resource")
                    elif event_type == "TERRITORY_CONFLICT":
                        event["factions"] = [m.group("attacker"), m.group("defender")]
                        event["damage"] = int(m.group("damage"))
                    elif event_type == "HARVEST_EVENT":
                        event["faction"] = m.group("faction")
                        event["food"] = float(m.group("food"))
                        event["wood"] = float(m.group("wood"))
                        event["ore"] = float(m.group("ore"))
                    elif event_type == "DEATH_EVENT":
                        event["npc"] = m.group("npc")
                    elif event_type == "STARVATION_EVENT":
                        event["faction"] = m.group("faction").strip()
                        event["count"] = int(m.group("count"))
                    elif event_type == "ALLIANCE_FORMED" or event_type == "TREATY_SIGNED":
                        event["factions"] = [m.group("faction1").strip(), m.group("faction2").strip()]
                    elif event_type == "WEATHER_EVENT":
                        event["event"] = m.group("event")
                    elif event_type == "TECH_UNLOCKED":
                        event["technology"] = m.group("tech")
                    elif event_type == "CULTURE_EVENT":
                        event["festival"] = m.group("festival")
                    elif event_type == "RITUAL_COMPLETED":
                        event["ritual"] = m.group("ritual")
                    elif event_type == "RESOURCE_DEPLETED" or event_type == "RESOURCE_DISCOVERED":
                        event["resource"] = m.group("resource")
                        event["location"] = {"x": int(m.group("x")), "y": int(m.group("y"))}
                    elif event_type == "LEADERSHIP_CHANGE":
                        event["faction"] = m.group("faction").strip()
                    elif event_type == "RUMOR_EVENT":
                        event["count"] = int(m.group(1))
                        event["tick"] = int(m.group(2))
                    elif event_type == "SAYING_EVENT":
                        event["count"] = int(m.group(1))
                        event["tick"] = int(m.group(2))
                    events.append(event)
                    matched_lines += 1
                    print(f"[DEBUG] Line {line_num}: Matched {event_type}: {line.strip()}", file=sys.stderr)
                    break
            if not matched:
                unmatched_lines += 1
                if unmatched_lines <= 10:
                    print(f"[DEBUG] Line {line_num}: No match: {line.strip()}", file=sys.stderr)
    print(f"[DEBUG] Total matched lines: {matched_lines}", file=sys.stderr)
    print(f"[DEBUG] Total unmatched lines: {unmatched_lines}", file=sys.stderr)
    return events

def bundle_events_by_era(events, ticks_per_era=TICKS_PER_ERA):
    eras = defaultdict(list)
    for event in events:
        era_start = (event["tick"] // ticks_per_era) * ticks_per_era
        era_end = era_start + ticks_per_era - 1
        eras[(era_start, era_end)].append(event)
    return eras

def generate_era_title(events):
    # Simple heuristic for era title
    if any(e["type"] == "TERRITORY_CONFLICT" for e in events):
        return "Era of Conflict"
    if any(e["type"] == "POPULATION_MILESTONE" for e in events):
        return "Era of Growth"
    return "Quiet Era"

def main():
    parser = argparse.ArgumentParser(description="Generate historian briefing from simulation log file.")
    parser.add_argument("--log-file", default="log.txt", help="Path to the log file to parse (default: log.txt)")
    parser.add_argument("--output", default=None, help="Path to output JSON file (default: stdout)")
    parser.add_argument("--ticks-per-era", type=int, default=TICKS_PER_ERA, help=f"Ticks per era (default: {TICKS_PER_ERA})")
    args = parser.parse_args()

    events = parse_events(args.log_file)
    eras = bundle_events_by_era(events, args.ticks_per_era)
    output = []
    for era_idx, ((start_tick, end_tick), era_events) in enumerate(sorted(eras.items())):
        era_title = generate_era_title(era_events)
        # Sort events by tick for deterministic output
        era_events_sorted = sorted(era_events, key=lambda e: e["tick"])
        # Simple summary: first, middle, last event types (for now)
        summary_points = []
        if era_events_sorted:
            if len(era_events_sorted) == 1:
                summary_points = [f"{era_events_sorted[0]['type']} at tick {era_events_sorted[0]['tick']}"]
            else:
                summary_points = [
                    f"{era_events_sorted[0]['type']} at tick {era_events_sorted[0]['tick']}",
                    f"{era_events_sorted[len(era_events_sorted)//2]['type']} at tick {era_events_sorted[len(era_events_sorted)//2]['tick']}",
                    f"{era_events_sorted[-1]['type']} at tick {era_events_sorted[-1]['tick']}"
                ]
        briefing = {
            "era_index": era_idx,
            "start_tick": start_tick,
            "end_tick": end_tick,
            "era_title": era_title,
            "summary": summary_points,
            "key_events": era_events_sorted
        }
        output.append(briefing)
    
    json_output = json.dumps(output, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"Briefing saved to {args.output}", file=sys.stderr)
    else:
        print(json_output)

if __name__ == "__main__":
    main()
