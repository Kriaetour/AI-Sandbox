from databank import get_databank


def main():
    db = get_databank()
    print("Categories:", db.list_categories())
    # Show weighted sampling demo
    db.add_entry("names", "Aurelion", rarity="legendary", tags=["myth"])
    db.add_entry("names", "Bran", rarity="common")
    db.add_entry("names", "Corlin", rarity="uncommon")
    print("Sample names (weighted):", db.get_random("names", count=5))
    # Filter: only entries tagged with 'myth'
    myth_names = db.get_random("names", count=2, predicate=lambda e: "myth" in e.get("tags", []))
    print("Myth-tagged names:", myth_names)
    # Tag existing
    db.tag_entry("sayings", "The river remembers every stone.", "foundational")
    foundational = db.get_random(
        "sayings", count=3, predicate=lambda e: "foundational" in e.get("tags", [])
    )
    print("Foundational sayings sample:", foundational)
    # Show persistence
    db.save()
    print("Databank saved to persistence/databank.json")


if __name__ == "__main__":
    main()
