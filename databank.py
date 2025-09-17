import random
import json
import os
from typing import List, Dict, Optional, Callable, Any, Union


class DataBank:
    """Central repository for large selectable cultural/gameplay lists.

    Provides up to 100 (or more) pre-seeded entries per category and safe random retrieval.
    Categories can be extended at runtime. Duplicate prevention and capped growth (default 100) enforced.
    """

    def __init__(
        self,
        max_entries_per_category: int = 100,
        autosave: bool = True,
        storage_path: str = os.path.join("persistence", "databank.json"),
    ):
        self.max_entries = max_entries_per_category
        self.autosave = autosave
        self.storage_path = storage_path
        # Data structure: category -> list of entries; entry can be str or dict with {'text': str, 'rarity': str, 'tags': [...]}.
        self._data: Dict[str, List[Union[str, Dict[str, Any]]]] = {}
        if not self._load():
            # Seed if file absent / invalid
            self._data = {
                "names": self._wrap_list(self._generate_name_pool(), tag="name"),
                "sayings": self._wrap_list(self._generate_sayings_pool(), tag="saying"),
                "spirit_guides": self._wrap_list(
                    self._generate_spirit_guides_pool(), tag="spirit_guide"
                ),
                "titles": self._wrap_list(self._generate_titles_pool(), tag="title"),
                "epithets": self._wrap_list(self._generate_epithets_pool(), tag="epithet"),
                "music_styles": self._wrap_list(self._generate_music_styles_pool(), tag="music"),
                "rumors": self._wrap_list(self._generate_rumors_pool(), tag="rumor"),
                "seasonal_rituals": self._wrap_list(
                    self._generate_seasonal_rituals_pool(), tag="ritual"
                ),
                "creation_myths": self._wrap_list(self._generate_creation_myths_pool(), tag="myth"),
                "tribe_prefixes": self._wrap_list(
                    self._generate_tribe_prefixes_pool(), tag="prefix"
                ),
                "tribe_suffixes": self._wrap_list(
                    self._generate_tribe_suffixes_pool(), tag="suffix"
                ),
            }
            # Apply default rarity gradients & semantic tags for deeper variety weighting
            self._apply_initial_rarity_and_tags()
            self._save()

    # ---- Persistence ----
    def _save(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            serializable = {}
            for cat, entries in self._data.items():
                serializable[cat] = []
                for e in entries:
                    if isinstance(e, dict):
                        serializable[cat].append(e)
                    else:
                        serializable[cat].append({"text": e, "rarity": "common", "tags": []})
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"max_entries": self.max_entries, "data": serializable},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            return True
        except Exception:
            return False

    def _load(self) -> bool:
        try:
            if not os.path.isfile(self.storage_path):
                return False
            with open(self.storage_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self.max_entries = payload.get("max_entries", self.max_entries)
            self._data = payload.get("data", {})
            return True
        except Exception:
            return False

    def save(self):
        self._save()

    # ---- Public API ----
    def get_random(
        self,
        category: str,
        count: int = 1,
        unique: bool = True,
        predicate: Optional[Callable[[Dict[str, Any]], bool]] = None,
    ) -> List[str]:
        entries = self._data.get(category, [])
        if not entries:
            return []
        # Normalize entries to dict form for weighting/predicate
        norm: List[Dict[str, Any]] = []
        for e in entries:
            if isinstance(e, dict):
                norm.append(e)
            else:
                norm.append({"text": e, "rarity": "common", "tags": []})
        if predicate:
            norm = [e for e in norm if predicate(e)]
        if not norm:
            return []
        # Rarity weighting
        weight_map = {"common": 1.0, "uncommon": 2.0, "rare": 4.0, "legendary": 7.0}
        weights = [weight_map.get(e.get("rarity", "common"), 1.0) for e in norm]
        results: List[str] = []
        if unique:
            # Sample without replacement manually using weights
            pool = list(norm)
            weight_pool = list(weights)
            for _ in range(min(count, len(pool))):
                total = sum(weight_pool)
                r = random.random() * total
                acc = 0.0
                idx = 0
                for i, w in enumerate(weight_pool):
                    acc += w
                    if r <= acc:
                        idx = i
                        break
                chosen = pool.pop(idx)
                weight_pool.pop(idx)
                results.append(chosen["text"])
        else:
            for _ in range(count):
                total = sum(weights)
                r = random.random() * total
                acc = 0.0
                chosen = norm[0]
                for e, w in zip(norm, weights):
                    acc += w
                    if r <= acc:
                        chosen = e
                        break
                results.append(chosen["text"])
        return results

    def add_entry(
        self,
        category: str,
        entry: str,
        rarity: str = "common",
        tags: Optional[List[str]] = None,
    ) -> bool:
        category = category.lower()
        if category not in self._data:
            self._data[category] = []
        # Prevent duplicates based on text
        for existing in self._data[category]:
            if (existing.get("text") if isinstance(existing, dict) else existing) == entry:
                return False
        if len(self._data[category]) >= self.max_entries:
            return False
        record = {"text": entry, "rarity": rarity, "tags": tags or []}
        self._data[category].append(record)
        if self.autosave:
            self._save()
        return True

    def ensure_category(self, category: str):
        if category not in self._data:
            self._data[category] = []

    def list_categories(self) -> List[str]:
        return sorted(self._data.keys())

    def get_all(self, category: str) -> List[str]:
        out = []
        for e in self._data.get(category, []):
            if isinstance(e, dict):
                out.append(e.get("text", ""))
            else:
                out.append(e)
        return out

    def get_all_entries(self, category: str) -> List[Dict[str, Any]]:
        entries = self._data.get(category, [])
        norm = []
        for e in entries:
            if isinstance(e, dict):
                norm.append(e)
            else:
                norm.append({"text": e, "rarity": "common", "tags": []})
        return norm

    def tag_entry(self, category: str, text: str, tag: str) -> bool:
        for e in self._data.get(category, []):
            if (e.get("text") if isinstance(e, dict) else e) == text:
                if isinstance(e, dict):
                    if "tags" not in e:
                        e["tags"] = []
                    if tag not in e["tags"]:
                        e["tags"].append(tag)
                        if self.autosave:
                            self._save()
                        return True
                return False
        return False

    def set_rarity(self, category: str, text: str, rarity: str) -> bool:
        for e in self._data.get(category, []):
            if (e.get("text") if isinstance(e, dict) else e) == text and isinstance(e, dict):
                e["rarity"] = rarity
                if self.autosave:
                    self._save()
                return True
        return False

    # ---- Helpers ----
    def _wrap_list(self, items: List[str], tag: Optional[str] = None) -> List[Dict[str, Any]]:
        wrapped = []
        for s in items:
            entry = {"text": s, "rarity": "common", "tags": []}
            if tag:
                entry["tags"].append(tag)
            wrapped.append(entry)
        return wrapped

    # ---- Internal Generators ----
    def _generate_name_pool(self) -> List[str]:
        prefixes = [
            "Ara",
            "Bel",
            "Cor",
            "Dra",
            "Ela",
            "Fae",
            "Gal",
            "Hel",
            "Ior",
            "Jun",
            "Kel",
            "Lyr",
            "Mor",
            "Nai",
            "Ori",
            "Pyr",
            "Qua",
            "Rin",
            "Syl",
            "Tor",
            "Umb",
            "Var",
            "Wyn",
            "Xil",
            "Yra",
            "Zor",
        ]
        suffixes = [
            "ana",
            "bris",
            "cor",
            "dun",
            "eris",
            "fira",
            "gorn",
            "hal",
            "ion",
            "jara",
            "kor",
            "lith",
            "mund",
            "nora",
            "phyra",
            "quis",
            "rith",
            "sara",
            "tor",
            "vash",
            "wyn",
            "xen",
            "yra",
            "zor",
        ]
        base = []
        for p in prefixes:
            for s in suffixes:
                if len(base) >= 100:
                    break
                base.append(p + s)
            if len(base) >= 100:
                break
        return base

    def _generate_sayings_pool(self) -> List[str]:
        sayings = [
            "The river remembers every stone.",
            "Honor grows where truth is spoken.",
            "A quiet fire warms the longest night.",
            "Trade is the breath between strangers.",
            "Spirits walk where stories live.",
            "Survival is a braided rope.",
            "Listen to the dusk; it hides tomorrow.",
            "Prosperity favors the patient gatherer.",
            "Our oath is older than the mountain.",
            "Shadows teach light its boundaries.",
            "Rain forgives the scorched earth.",
            "The spear flies straighter in silence.",
            "Two tribes share one horizon.",
            "Buried embers still remember flame.",
            "A myth begins as a single careful word.",
            "The wary path avoids needless conflict.",
            "Stone holds the memory of storms.",
            "Wealth without ritual is an empty bowl.",
            "Winds carry the unguarded promise.",
            "Dawn does not bargain with the night.",
            "A guide of spirits walks between breaths.",
            "Trade roots become alliance branches.",
            "Songs mend what iron cannot.",
            "Blood cools faster than resentment.",
            "Shared ritual builds unseen walls.",
            "Rain answers the unasked thirst.",
            "No boundary survives a patient root.",
            "Quiet strength is still strength.",
            "Stories travel farther than scouts.",
            "The wary hunter thanks the fallen.",
            "Fortune circles like a hawk.",
            "We survive by weaving differences.",
            "A kept promise feeds many winters.",
            "Old fire, new warmth.",
            "The earth keeps its true ledger.",
            "A blade of honor dulls in deceit.",
            "Trade before raid when roads are open.",
            "Even silence has a dialect.",
            "The patient forge shapes truer tools.",
            "Roots of kinship find water deep.",
            "A drifting value erodes a tribe.",
            "Lexicon growth is cultural breath.",
            "Rituals are stories you can stand inside.",
            "Myths harvest meaning from chaos.",
            "Diffusion is the silent teacher.",
            "Shared symbols reduce sharp edges.",
            "Value drift reveals cultural fatigue.",
            "Language evolves like thawed rivers.",
            "Every adopted rite changes two fires.",
            "Conflict writes harsher proverbs.",
        ]
        return sayings[:100]

    def _generate_spirit_guides_pool(self) -> List[str]:
        guides = [
            "Ashwolf",
            "Blue Heron",
            "Cinder Stag",
            "Dawn Serpent",
            "Echo Lynx",
            "Frost Crow",
            "Glacier Bear",
            "Hearth Owl",
            "Iron Tortoise",
            "Jade Viper",
            "Kindled Moth",
            "Lumen Elk",
            "Mist Panther",
            "Night Kestrel",
            "Obsidian Fox",
            "Pale Salmon",
            "Quill Boar",
            "River Drake",
            "Stone Warden",
            "Thorn Hare",
            "Umber Lion",
            "Verdant Dormouse",
            "Whisper Bat",
            "Xyrel Mantis",
            "Yellow Pike",
            "Zephyr Hare",
            "Ancient Tortoise",
            "Star Pike",
            "Dust Wren",
            "Spirit Moth",
            "Horizon Wolf",
            "Moss Elk",
            "Tide Jaguar",
            "Storm Ibex",
            "Spiral Falcon",
            "Mirror Trout",
            "Snowback Ape",
            "Lantern Beetle",
            "Bramble Hare",
            "Pulse Wasp",
            "Silver Caribou",
            "Crested Raven",
            "Lowland Lynx",
            "Sunscale Newt",
            "Thornback Trout",
            "Farstep Fox",
            "Highplains Hare",
            "Sunstripe Owl",
            "Cloudback Bison",
            "Rune Owl",
        ]
        return guides[:100]

    def _generate_titles_pool(self) -> List[str]:
        return [
            "Keeper of Embers",
            "Voice of Stone",
            "Watcher of Horizons",
            "Bearer of the First Flame",
            "Oath Weaver",
            "Storm Listener",
            "Ritesmith",
            "Myth Binder",
            "Speaker for Rivers",
            "Shell of Dawn",
            "Memory Carrier",
            "Warden of Ashes",
            "Spiral Walker",
            "Guide of Eight Winds",
            "Song Archivist",
            "Chain of Accord",
            "Harbinger of Renewal",
            "Silent Mediator",
            "Bone Interpreter",
            "Flame Iterant",
            "Cycle Witness",
            "Glyph Herald",
            "Rift Watcher",
            "Pact Gardener",
        ][:100]

    def _generate_epithets_pool(self) -> List[str]:
        return [
            "the Dawnlit",
            "the Riverborn",
            "the Emberkept",
            "the Silent Step",
            "the Ash-Marked",
            "the Nine-Tongued",
            "the Rootwise",
            "the Skybound",
            "the Stonefast",
            "the Drift-Watcher",
            "the Frost-Pledged",
            "the Myth-Maker",
            "the Trade-Warm",
            "the Pact-Forged",
            "the Storm-Steady",
            "the Far-Listened",
            "the Boundless",
            "the Spirit-Favored",
            "the Rift-Minded",
            "the Hearth-Sworn",
        ][:100]

    def _generate_music_styles_pool(self) -> List[str]:
        styles = [
            "syncopated bone flute duets",
            "low canyon horn calls",
            "ritual shell chime cascades",
            "layered dusk drum pulses",
            "reed flute echo rounds",
            "ember-circle heartbeat drumming",
            "glacial bell strikes",
            "rain-bowl water drips ensemble",
            "braided throat harmony drones",
            "three-tone river whistle sets",
            "hollow log resonant pounding",
            "stone disk rotational ringing",
            "spindle hum accompaniment",
            "wind sleeve flutter chorus",
            "antler frame rattling cycles",
            "shell anklet migration rhythms",
            "call-and-response ridge chants",
            "twilight ember hush humming",
            "woven bark string plucking",
            "obsidian shard chime falls",
            "fog horn conch laments",
            "spring thaw splash patterns",
            "ancestral name weaving songs",
            "trade-route tempo blending",
            "five-breath interval chanting",
            "spiral path walking cadence",
            "lunar phase overtone ringing",
            "harvest mortar rhythmic pounding",
            "echo cave pulse returns",
            "meadow wingbeat imitation",
            "river stone skip clacks",
            "braid-tension board twanging",
            "ocean spray drift whistling",
            "root hollow depth booming",
            "pine needle rain shivers",
            "distant storm roll mimicry",
            "sunshaft crystal prismatic tones",
            "migratory flock scatter calls",
            "ceremonial ash swirl rattles",
            "nocturne ember crackle choir",
            "tendon string bowed resonance",
            "seed pod shaker lattices",
            "heated clay pop percussion",
            "evening fog layer drones",
            "territory border low hum line",
            "tribute ancestor cadence recitals",
            "braided reed pan-harmonies",
            "frozen branch friction singing",
            "spirit-guide mimic sequences",
            "dawn frost crunch tempo",
            "ember-cooling ticking arrays",
            "salt flat reflective claps",
            "tidal pool bubble rhythms",
            "glowworm pulse timing accompaniment",
            "copper vein resonance tapping",
            "molten sand hiss accents",
            "woven sail wind harp tones",
            "pillar cast echo spirals",
            "storm shelter breath unison",
            "trade oath metric recitation",
            "dawn perimeter watch cadence",
            "forge spark scatter bells",
            "harbor mast tension drones",
            "granary basket thump meters",
            "ancestor mask amplification chants",
            "glimmer fish scale rattles",
            "snowpack compression cadence",
            "glacial melt channel whistles",
            "twined cord rotational humming",
            "charcoal grind soft scrapes",
            "floodplain reed ripple tremors",
            "dry basin bone shard clicks",
            "obsidian dust rain hiss",
            "tidal gate chain resonance",
            "braided rope pluck ostinatos",
            "fireline advance tempo markers",
            "scout recall distance horns",
            "moonwell surface agitation tones",
            "blessing circle rising triads",
            "vigil torch phasing hums",
            "perimeter ward pulse knocks",
            "spirit appeasement falling fifths",
            "seed permutation counting songs",
            "artifact unveiling suspended tones",
            "victory ash dispersal chorus",
            "night crossing synchronized breaths",
            "dawn emergence interval bells",
            "harvest gratitude descending ladders",
            "founding myth recenter drones",
            "lexicon expansion syllable chimes",
            "treaty knot tying pulses",
            "conflict mourning hollow chords",
            "winter shelter heart-slow drums",
            "solstice angle sunbeam harps",
            "ember ledger tally taps",
            "ritual silence framing tones",
            "long memory low root drones",
            "river mouth salt reed blends",
            "ancestral echo call braids",
            "migratory path lattice pulses",
        ]
        return styles[:100]

    def _generate_rumors_pool(self) -> List[str]:
        entries = [
            "A hidden cache lies beneath the split cedar.",
            "The northern pass tribe courts a storm spirit.",
            "Trade scouts vanished near the ash flats.",
            "A spirit guide changed allegiance at dawn.",
            "Two rival smiths forged a single oath blade.",
            "An unmarked banner was seen beyond the ridge.",
            "A river braid is shifting; fisheries may fail.",
            "Night fires mapped a message across terraces.",
            "A pact token cracked without touch.",
            "Stone listeners heard hollow thunder underground.",
            "An envoy returned speaking in borrowed dialect.",
            "Skywatchers charted a silent comet recursion.",
            "Ancestral masks wept resin at moonrise.",
            "Border drums skipped a protective cadence.",
            "Foragers found glyphs older than root depth.",
            "A migrating herd reversed direction twice.",
            "Harvest jars sealed themselves before cooling.",
            "A trade oath was recited backward successfully.",
            "Three scouting crows refused elevation.",
            "A frost line formed inside a summer kiln.",
            "River reeds hummed treaty intervals unbidden.",
            "A bone charm spun against prevailing wind.",
            "Two flame basins extinguished simultaneously.",
            "A myth fragment matched foreign verse exactly.",
            "Shell counters aligned into a trade ratio.",
            "Wind sleeves pulsed without atmospheric shift.",
            "Silent drum skins tightened at dusk.",
            "A salt ridge formed where none stood prior.",
            "Guide stones warmed before a conflict parley.",
            "Mist parted in hexagonal tessellation.",
            "Echo caves repeated unspoken treaty terms.",
            "Scout markings rearranged during rainfall.",
            "A tethered beacon line vibrated warning mode.",
            "New sprouts traced a migration spiral.",
            "Obsidian shards floated in boiling spring.",
            "An oath keeper lost memory of a sealed pact.",
            "River foam spelled a clan sigil.",
            "Map charcoal smeared into navigable channels.",
            "Sky fire reflected no color on bronze mirror.",
            "Ancestor tablets rotated on their own axis.",
            "A dormant kiln exhaled pollen.",
            "Ice lens formed over ember stones.",
            "Moored canoes drifted upriver briefly.",
            "Dune crest ripples encoded counting knots.",
            "A messenger owl delivered twice-copied bark.",
            "Hearth ash aligned like migration teeth.",
            "Camp perimeter pegs rose overnight.",
            "A water gauge sang descending thirds.",
            "Granary seal twine uncoiled without fray.",
            "Drift nets tangled into lattice glyphs.",
            "Wayfinding rods quivered toward inland void.",
            "Shell weight sets balanced uneven loads.",
            "Carved oath rings contracted painfully.",
            "Tide markers glowed during new moon.",
            "A scouting spear magnetized to basalt.",
            "Linguists recorded vowel shift contagion.",
            "Trade beads fused into a knot cluster.",
            "A dust front halted at border stakes.",
            "Pack harness bells rang treaty intervals.",
            "A rival claims your spirit guide's twin.",
            "Song keepers refused a dissonant interval.",
            "Fresh tracks overlapped in mirrored stride.",
            "Blood sap seeped from uncut bark.",
            "A woven banner resisted directional wind.",
            "Harbor float markers sank in rhythm.",
            "Night watch reported horizon glow pulses.",
            "A memory cord shed color segments.",
            "Two alloys blended along cooling seam.",
            "Perimeter ward stones inverted order.",
            "A relay whistle produced subharmonics.",
            "Boundary stream reversed for eight breaths.",
            "An unaligned artisan requested neutral sanction.",
            "Omen tablets softened then rehardened.",
            "A silence pocket followed the envoy home.",
            "New hatchling feathers showed treaty dyes.",
            "An oath ledger page duplicated itself.",
            "Distant thunder repeated prime factors.",
            "Dawn fog carried structured cadence.",
            "A supply caravan split without quarrel.",
            "Root cellar moisture crystallized patterns.",
            "Two clans traded unfinished ritual steps.",
            "A hunting whistle answered itself thrice.",
            "A drift beacon changed pulse phase.",
            "A pact forge cooled faster than stone.",
            "Sky lattice kites tangled in numeric weave.",
            "A blessed spring lowered one span.",
            "A lens stone focused moon heat.",
            "A gem inlay rearranged faction order.",
            "Smoke plumes stacked in discrete layers.",
            "Ancient boundary stakes resurfaced intact.",
            "A silent envoy carried dual faction seals.",
            "Midnight watch lost an hour of recall.",
            "Glacial melt taste shifted metallic.",
            "A copper tally rod shortened a notch.",
            "Ceremonial dye reversed pigment layers.",
            "A raven dropped a sealed trade bead.",
            "A valley echo returned extra syllables.",
            "An offering bowl overflowed unsourced water.",
            "Harbor rope fibers hummed tri-tone.",
            "Oath review stones felt lighter today.",
            "A horizon beacon spark jumped gap.",
            "Granite etch marks healed overnight.",
        ]
        return entries[:100]

    def _generate_seasonal_rituals_pool(self) -> List[str]:
        return [
            "first thaw river blessing",
            "spring seed memory braiding",
            "early flood channel mapping",
            "dawn mist ancestor whisper",
            "solstice ember renewal arch",
            "river confluence vow exchange",
            "migration path smoke tracing",
            "new moon silence lattice",
            "harvest storage seal rite",
            "granary spirit appeasement",
            "edge fire containment chant",
            "storm front vigilance ward",
            "dry season well descent",
            "ashen grove regrowth marking",
            "equinox dual flame balance",
            "long shadow perimeter calibration",
            "first frost shelter layering",
            "wolf star ascent calling",
            "leaf-fall residue sweeping",
            "root depth honoring walk",
            "spillway gate joint oiling",
            "clay kiln gratitude circle",
            "tidal retreat channel clearing",
            "braid cord tension renewal",
            "wind break lattice inspection",
            "ice lens sun focusing",
            "mooring rope fiber blessing",
            "guardian post resonance tapping",
            "memory cord dye refresh",
            "forge vent purge spiral",
            "hunting range ash masking",
            "salt ridge perimeter sweep",
            "drought watch vessel rationing",
            "pollinator drift welcome",
            "ridge echo calibration chant",
            "spirit guide effigy airing",
            "moon phase vow restatement",
            "sling stone balance test",
            "ancestral ledger recount",
            "shared myth recitation ring",
            "oath token weight audit",
            "soil salinity stirring walk",
            "herd path trample mitigation",
            "storm shelter brace tensioning",
            "artifact vault seal re-inking",
            "root cellar humidity rake",
            "ember pit thermal layering",
            "canoe hull pitch infusion",
            "beacon mast joint wrapping",
            "tri-tribe neutral oath renewal",
            "treaty knot lattice weaving",
            "fireline gap brush clearing",
            "fallow rotation map update",
            "scout relay whistle retune",
            "water table seep reading",
            "meteor watch posture training",
            "lexicon branch adoption chant",
            "distant trade roster calling",
            "sun spear angle resetting",
            "mid-winter silence inversion",
            "spore bloom containment ring",
            "border glyph repainting",
            "neutral ground ash levelling",
            "envoy path stone washing",
            "lunar tide harmonic test",
            "night crossing pace alignment",
            "sustenance jar vacuum check",
            "weaving frame tension audit",
            "ash vent updraft timing",
            "alliance roster memory call",
            "bark tannin leach cycle",
            "ceremonial dye viscosity test",
            "ferment vessel gas purge",
            "spindle weight recalibration",
            "drainage ditch debris rake",
            "post-thaw footing inspection",
            "bale stack compression measure",
            "ice anchor rope rewind",
            "root graft boundary walk",
            "alignment torch wick trimming",
            "syllable drift lexicon review",
            "guidestone thermal reading",
            "canoe draft displacement test",
            "sun disk shadow parity check",
            "triple hearth smoke convergence",
            "granary ring pest barrier",
            "spirit effigy pigment refresh",
            "harvest crate joint tapping",
            "trade bead density audit",
            "founding myth full reenactment",
        ][:100]

    def _generate_creation_myths_pool(self) -> List[str]:
        return [
            "born from entwined river braids under auroral arc",
            "etched from glacier retreat memory",
            "raised by basalt pillars after sky fracture",
            "sung forth by resonance of ten hollow stones",
            "spun from ember drift caught in first storm spiral",
            "woven by tidal reeds at triple moon alignment",
            "charted in mist before language crystallized",
            "awoken by migrating herd convergence",
            "lifted from sediment of collapsed dune sea",
            "kindled in obsidian bowl during silence cycle",
            "forged from alloy of eight sworn pacts",
            "shaded into being by eclipse scaffold",
            "gathered from bone flute overtones",
            "seeded in root mesh beneath thermal spring",
            "aligned by five converging shadow lengths",
            "cast from reflection of inverted dawn",
            "bound by trade ring of uncut copper",
            "distilled from first condensation on kiln lip",
            "remembered into shape by ancestral ledger keepers",
            "extracted from deep resonance fault line",
            "coalesced around drifting treaty ember",
            "decoded from rain spatter on unfired clay",
            "drawn from void left by retreating flood",
            "sustained by migration spiral watchers",
            "lifted from script of vanished survey rods",
            "mirrored from sky lattice kite angles",
            "stabilized by braided oath tension",
            "ascended from sun shaft through cavern mist",
            "molded by echo recursion in archive hall",
            "condensed from pact keeper exhalations",
            "harvested from shimmering pollen vortex",
            "charted by star loom calibrators",
            "translated from pre-lexicon pulse thrum",
            "surveyed from ridge triangulation fires",
            "drifted from ash stratification bands",
            "fortified by root boundary listeners",
            "clarified by meltwater filtration chorus",
            "stepped out of stasis of balanced scales",
            "rallied by convergence of fracture lines",
            "sifted from resonance sand amphitheater",
            "caught in eddy of tidal reversal",
            "woven from hair of twelve envoys",
            "summoned by lowland vapor ring",
            "raised by thermal updraft harness",
            "parametrized by counting knot savants",
            "emerged from stillness of conflict pause",
            "sealed by reciprocated offering sequences",
            "anchored by guide stone triangulation",
            "echo-modeled from canyon pulse returns",
            "incanted from ledger of unused names",
            "debugged from failed ritual permutations",
            "lifted from sleeping glacier fracture",
            "murmured by nocturnal perimeter watch",
            "stamped from alloy mold fracture pattern",
            "twined from dual rope under tension audit",
            "resolved from harmonic drift alignment",
            "grown from mineral accretion scaffolds",
            "retained after memory cord purge attempt",
            "precipitated from kiln exhaust condensation",
            "extrapolated from early trade imbalance",
            "scaffolded by neutral ground vow loop",
            "condensed out of overlapping treaty echoes",
            "iterated from myth fragment recombination",
            "pinned by survey stake constellation",
            "retrieved from spectral archive leakage",
            "sustained by coalition hum chorus",
            "declared by dawn sentinel redundancy",
            "spliced from twin dialect branch roots",
            "seeded by ember ledger recalculation",
            "reforged after conflict pattern inversion",
            "reissued by oath ring resonance",
            "secured by boundary peg harmonic",
            "distilled from flood recession timing",
            "formalized by lexicon drift moderators",
            "forged during root depth re-assessment",
        ][:100]

    def _generate_tribe_prefixes_pool(self) -> List[str]:
        return [
            "River",
            "Stone",
            "Forest",
            "Mountain",
            "Desert",
            "Plains",
            "Valley",
            "Canyon",
            "Coast",
            "Island",
            "Peak",
            "Summit",
            "Grove",
            "Thicket",
            "Meadow",
            "Prairie",
            "Marsh",
            "Swamp",
            "Lake",
            "Stream",
            "Creek",
            "Hill",
            "Ridge",
            "Cliff",
            "Cave",
            "Spring",
            "Falls",
            "Bay",
            "Harbor",
            "Glade",
            "Frost",
            "Ash",
            "Shadow",
            "Copper",
            "Obsidian",
            "Echo",
            "Storm",
            "Dawn",
            "Dusk",
            "Ember",
            "Mist",
            "Horizon",
            "Spirit",
            "Root",
            "Sky",
            "Wind",
            "Wave",
            "Tide",
            "Thunder",
        ][:100]

    def _generate_tribe_suffixes_pool(self) -> List[str]:
        return [
            "folk",
            "tribe",
            "clan",
            "people",
            "guardians",
            "keepers",
            "walkers",
            "hunters",
            "gatherers",
            "builders",
            "weavers",
            "smiths",
            "farmers",
            "fishers",
            "herders",
            "riders",
            "dwellers",
            "settlers",
            "nomads",
            "warriors",
            "shamans",
            "elders",
            "spirits",
            "winds",
            "stars",
            "singers",
            "tenders",
            "wardens",
            "seekers",
            "casters",
        ][:100]

    # ---- Post-Seed Rarity & Tagging ----
    def _apply_initial_rarity_and_tags(self):
        try:
            # Creation myths: later entries (structurally more complex) get higher rarity tiers
            myths = self._data.get("creation_myths", [])
            for idx, entry in enumerate(myths):
                if not isinstance(entry, dict):
                    continue
                # Simple gradient mapping based on index percentile
                pct = (idx + 1) / max(1, len(myths))
                if pct > 0.85:
                    entry["rarity"] = "legendary"
                    entry["tags"].append("esoteric")
                elif pct > 0.65:
                    entry["rarity"] = "rare"
                    entry["tags"].append("ancient")
                elif pct > 0.40:
                    entry["rarity"] = "uncommon"
                    entry["tags"].append("foundational")
                else:
                    entry["rarity"] = "common"
                    entry["tags"].append("core")

            # Rumors: tag pattern groups based on keywords
            rumor_patterns = [
                ("treaty", "diplomatic"),
                ("oath", "diplomatic"),
                ("envoy", "diplomatic"),
                ("spirit", "spiritual"),
                ("guide", "spiritual"),
                ("ancestor", "heritage"),
                ("glyph", "archaeic"),
                ("echo", "acoustic"),
                ("rift", "anomaly"),
                ("fault", "geologic"),
                ("basalt", "geologic"),
                ("shard", "material"),
                ("alloy", "material"),
                ("fog", "atmospheric"),
                ("thunder", "atmospheric"),
                ("comet", "astral"),
                ("moon", "astral"),
                ("star", "astral"),
            ]
            rumors = self._data.get("rumors", [])
            for r in rumors:
                if not isinstance(r, dict):
                    continue
                text = r.get("text", "").lower()
                # Base rarity default
                r["rarity"] = "common"
                assigned = False
                for kw, tag in rumor_patterns:
                    if kw in text:
                        if tag not in r["tags"]:
                            r["tags"].append(tag)
                        assigned = True
                if not assigned:
                    r["tags"].append("ambient")
                # Elevate rarity for certain complex structural hints
                triggers = [
                    "simultaneously",
                    "rearranged",
                    "inverted",
                    "duplicate",
                    "fracture",
                    "alignment",
                ]
                if any(t in text for t in triggers):
                    r["rarity"] = "uncommon"
                if "legendary" in r["tags"]:
                    r["rarity"] = "legendary"
        except Exception:
            pass


# Singleton style access
GLOBAL_DATABANK: Optional[DataBank] = None


def get_databank() -> DataBank:
    global GLOBAL_DATABANK
    if GLOBAL_DATABANK is None:
        GLOBAL_DATABANK = DataBank()
    return GLOBAL_DATABANK
