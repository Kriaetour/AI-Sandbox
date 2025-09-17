import os
import json
import random
from collections import defaultdict, Counter, deque
from typing import Dict, List, Tuple, Optional

# ---------------------------------------------------------------------------
# Clean Rebuild (strict dual-model Markov dialogue with variation + diversity)
# ---------------------------------------------------------------------------
# Features restored & integrated:
# - Separate hostile vs neutral trigram models with hard lexical separation
# - Sanitized adaptive learning (neutral lines strip hostile lexicon)
# - Persistence for strict models
# - Recent memory, bigram overlap filtering, frequency penalty, rare-token boost
# - Public APIs: generate_markov_dialogue, learn_dialogue, extend_dialogue_corpus, flush_dialogue_state

CLEAN_SLATE_ISOLATION = True
USE_STRICT_CONDITIONAL = True
STRICT_PERSISTENCE = True

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
STRICT_STATE_DIR = os.path.join(_MODULE_DIR, "persistence", "language_analytics")
STRICT_HOSTILE_STATE = os.path.join(STRICT_STATE_DIR, "strict_hostile_model.json")
STRICT_NEUTRAL_STATE = os.path.join(STRICT_STATE_DIR, "strict_neutral_model.json")
STATS_STATE = os.path.join(STRICT_STATE_DIR, "dialogue_diversity_stats.json")

# Variation + diversity knobs
_RECENT_MEMORY_MAXLEN = 10  # window of last lines to avoid immediate repeats
_VARIATION_RESAMPLE_ATTEMPTS = 5  # attempts to find alternate line
_BIGRAM_OVERLAP_THRESHOLD = 0.55  # similarity cutoff vs previous line
_FREQ_PENALTY_WEIGHT = 0.6  # weight penalizing frequent lines
_RARE_TOKEN_BOOST = 0.9  # weight boosting lines with rarer tokens
_RARE_TOKEN_THRESHOLD = 2  # token freq <= threshold counts as rare

# Data structures for diversity accounting
_RECENT_MEMORY: Dict[str, deque] = defaultdict(lambda: deque(maxlen=_RECENT_MEMORY_MAXLEN))
_FREQ_STATS: Dict[str, Counter] = defaultdict(Counter)  # line frequency per context
_TOKEN_STATS: Dict[str, Counter] = defaultdict(Counter)  # token frequency per context

# Hostile lexicon separation
_STYLE_LEXICON = {
    "hostility": ["back", "leave", "challenge", "threat", "force", "stand", "caution"],
    "encounter": ["greetings", "hello", "well", "met", "share"],
    "idle": ["weather", "stories", "happening", "new"],
    "trade": ["trade", "exchange", "deal", "goods", "surplus"],
    "peace": ["peace", "harmony", "together", "accord"],
}

# Seed corpora (clean + expanded)
DIALOGUE_CORPORA: Dict[str, List[str]] = {
    "encounter": [
        "Hello there! Greetings, friend, well met.",
        "What do you want, and state your business, approach with caution.",
        "Peace be with you, may we share this moment, greetings in harmony.",
        "We travel lightly, and seek only knowledge and kinship.",
        "Our fires burn warm, and we welcome calm exchange of news.",
        "Let us speak plainly, and learn from each other's journeys.",
        "Traveler, your footsteps carry distant dust, tell us what horizons you crossed.",
        "May the path between our camps stay open, and generous.",
        "Stories carried on wandering boots weave new kinship tonight, and bind us as friends.",
        "Share a fragment of your road, and we will match it with our own, so all may learn.",
        "We gather here, and though the night is cold, our words bring warmth.",
        "If you are lost, or simply wandering, you are welcome by our fire.",
    ],
    "trade": [
        "Care to trade, I have goods to offer, let's make a deal.",
        "Take what you need, I share freely, let me help you.",
        "Fair exchange strengthens the path between our fires, and builds trust.",
        "Goods well matched bring mutual prosperity, and lasting accord.",
        "Barter in goodwill, and both camps sleep with lighter worries.",
        "Lay out your surplus, and I will set mine beside it for balance.",
        "Let the scale be stories as well as items, so all profit.",
        "Your pack seems heavy, perhaps a fair swap lightens both our burdens.",
        "If you have salt, and I have grain, together we can feast.",
        "Trade is the bridge between strangers, and the root of friendship.",
    ],
    "idle": [
        "Nice weather today, how are you, what's new?",
        "Tell me about yourself, what's been happening, I am fascinated by your stories.",
        "Stories bind memory to the living moment, and echo in the heart.",
        "Have you seen the sky at dawn, it promises gentle hours ahead.",
        "I listen for distant drums, mostly I hear only wind and promise.",
        "The evening mist settles softly over quiet embers, and brings peace.",
        "Sometimes silence teaches more than crowded councils ever could, and wisdom grows.",
        "I mark time by the way shadows lean across the river stones, and the sun's slow arc.",
        "Do you keep a small ritual that steadies you each morning, or do you wander free?",
        "Quiet rivers reflect patient stories tonight, and the stars listen in silence.",
        "Calm sharing builds accord among wanderers, and trust grows with every word.",
    ],
    "hostility": [
        "Stay back, this is my territory, leave now!",
        "You dare challenge me, back off or face consequences, this ends now!",
        "If you cross this line, and threaten my kin, you will regret it.",
        "I do not want trouble, but I will defend what is mine, so beware.",
    ],
}


# ---------------------------------------------------------------------------
# Core N-gram model
# ---------------------------------------------------------------------------
class NGramMarkov:
    def __init__(self, n: int = 3):
        self.n = max(2, n)
        self.model: Dict[Tuple[str, ...], Counter] = defaultdict(Counter)
        self.starts_by_context: Dict[str, List[Tuple[str, ...]]] = defaultdict(list)
        self.raw_lines: Dict[str, List[str]] = defaultdict(list)

    def _tokenize(self, line: str) -> List[str]:
        return [w for w in line.strip().split() if w]

    def train_context(self, context: str, lines: List[str]):
        for line in lines:
            self.add_line(context, line, train_immediately=False)
        self._rebuild()

    def add_line(self, context: str, line: str, train_immediately: bool = True):
        if not line:
            return
        self.raw_lines[context].append(line)
        if train_immediately:
            self._update_line(context, line)

    def _update_line(self, context: str, line: str):
        tokens = self._tokenize(line)
        if not tokens:
            return
        padded = tokens + [None]
        start_len = self.n - 1
        if len(tokens) >= start_len:
            self.starts_by_context[context].append(tuple(tokens[:start_len]))
        else:
            self.starts_by_context[context].append(tuple(tokens))
        for i in range(len(padded)):
            window = padded[i : i + self.n]
            if len(window) < self.n:
                break
            *hist, nxt = window
            hist_t = tuple(hist)
            self.model[hist_t][nxt] += 1

    def _rebuild(self):
        self.model.clear()
        self.starts_by_context.clear()
        for ctx, lines in self.raw_lines.items():
            for line in lines:
                self._update_line(ctx, line)

    def all_starts(self) -> List[Tuple[str, ...]]:
        acc: List[Tuple[str, ...]] = []
        for lst in self.starts_by_context.values():
            acc.extend(lst)
        return acc

    def generate(self, max_words: int = 20) -> List[str]:
        all_starts = self.all_starts()
        if not self.model or not all_starts:
            return []
        start = random.choice(all_starts)
        generated = list(start)
        usage = Counter(generated)
        rep_penalty = 1.05
        for _ in range(max_words - len(start)):
            progressed = False
            for backoff in range(self.n - 1, 0, -1):
                hist = tuple(generated[-backoff:])
                if hist in self.model:
                    choices = self.model[hist]
                    weighted = []
                    for tok, cnt in choices.items():
                        if tok is None:
                            weighted.append((tok, cnt))
                            continue
                        base = float(cnt)
                        if usage[tok] > 0:
                            base /= rep_penalty ** usage[tok]
                        weighted.append((tok, base))
                    total = sum(w for _, w in weighted if w > 0)
                    if total <= 0:
                        continue
                    r = random.random() * total
                    cum = 0.0
                    next_tok = None
                    for tok, w in weighted:
                        cum += w
                        if cum >= r:
                            next_tok = tok
                            break
                    if next_tok is None:
                        progressed = True
                        break
                    generated.append(next_tok)
                    usage[next_tok] += 1
                    progressed = True
                    break
            if not progressed:
                break
        return [t for t in generated if t is not None]

    def to_state(self):
        return {"n": self.n, "raw_lines": self.raw_lines}

    @classmethod
    def from_state(cls, state):
        inst = cls(n=state.get("n", 3))
        inst.raw_lines = defaultdict(
            list, {k: list(v) for k, v in state.get("raw_lines", {}).items()}
        )
        inst._rebuild()
        return inst


# ---------------------------------------------------------------------------
# Global strict models
# ---------------------------------------------------------------------------
_STRICT_HOSTILE_MODEL: Optional[NGramMarkov] = None
_STRICT_NEUTRAL_MODEL: Optional[NGramMarkov] = None

# ---------------------------------------------------------------------------
# Build / load strict models
# ---------------------------------------------------------------------------


def _sanitize_neutral_line(line: str) -> str:
    hostile_set = set(_STYLE_LEXICON["hostility"]) | {"territory", "challenge", "dare"}
    kept = []
    for tok in line.split():
        if tok.lower().strip(".,!?") in hostile_set:
            continue
        kept.append(tok)
    return " ".join(kept)


def _build_strict_models():
    global _STRICT_HOSTILE_MODEL, _STRICT_NEUTRAL_MODEL
    if _STRICT_HOSTILE_MODEL and _STRICT_NEUTRAL_MODEL:
        return _STRICT_HOSTILE_MODEL, _STRICT_NEUTRAL_MODEL
    if STRICT_PERSISTENCE:
        try:
            if os.path.exists(STRICT_HOSTILE_STATE):
                with open(STRICT_HOSTILE_STATE, "r", encoding="utf-8") as f:
                    hs = json.load(f)
                _STRICT_HOSTILE_MODEL = NGramMarkov.from_state(hs)
        except Exception:
            _STRICT_HOSTILE_MODEL = None
        try:
            if os.path.exists(STRICT_NEUTRAL_STATE):
                with open(STRICT_NEUTRAL_STATE, "r", encoding="utf-8") as f:
                    ns = json.load(f)
                _STRICT_NEUTRAL_MODEL = NGramMarkov.from_state(ns)
        except Exception:
            _STRICT_NEUTRAL_MODEL = None
        # Load diversity stats if present
        if os.path.exists(STATS_STATE):
            try:
                with open(STATS_STATE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                _FREQ_STATS.clear()
                for ctx, mapping in data.get("freq_stats", {}).items():
                    ctr = Counter(mapping)
                    _FREQ_STATS[ctx] = ctr
                _TOKEN_STATS.clear()
                for ctx, mapping in data.get("token_stats", {}).items():
                    ctr = Counter(mapping)
                    _TOKEN_STATS[ctx] = ctr
                _RECENT_MEMORY.clear()
                for ctx, lines in data.get("recent_memory", {}).items():
                    dq = deque(maxlen=_RECENT_MEMORY_MAXLEN)
                    for ln in lines[-_RECENT_MEMORY_MAXLEN:]:
                        dq.append(ln)
                    _RECENT_MEMORY[ctx] = dq
            except Exception:
                pass
        if _STRICT_HOSTILE_MODEL and _STRICT_NEUTRAL_MODEL:
            return _STRICT_HOSTILE_MODEL, _STRICT_NEUTRAL_MODEL
    # fresh build
    h = NGramMarkov(3)
    n = NGramMarkov(3)
    # hostile
    h.train_context("hostility", DIALOGUE_CORPORA["hostility"])
    # neutral contexts sanitized
    hostile_set = set(_STYLE_LEXICON["hostility"]) | {"territory", "challenge", "dare"}
    for ctx, lines in DIALOGUE_CORPORA.items():
        if ctx == "hostility":
            continue
        sanitized = []
        for ln in lines:
            toks = [t for t in ln.split() if t.lower().strip(".,!?") not in hostile_set]
            if toks:
                sanitized.append(" ".join(toks))
        n.train_context(ctx, sanitized)
    _STRICT_HOSTILE_MODEL = h
    _STRICT_NEUTRAL_MODEL = n
    return _STRICT_HOSTILE_MODEL, _STRICT_NEUTRAL_MODEL


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------


def _save_strict():
    if not STRICT_PERSISTENCE:
        return
    if not (_STRICT_HOSTILE_MODEL and _STRICT_NEUTRAL_MODEL):
        return
    os.makedirs(STRICT_STATE_DIR, exist_ok=True)
    try:
        with open(STRICT_HOSTILE_STATE, "w", encoding="utf-8") as f:
            json.dump(_STRICT_HOSTILE_MODEL.to_state(), f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    try:
        with open(STRICT_NEUTRAL_STATE, "w", encoding="utf-8") as f:
            json.dump(_STRICT_NEUTRAL_MODEL.to_state(), f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    # Persist diversity stats
    try:
        stats_payload = {
            "freq_stats": {ctx: dict(counter) for ctx, counter in _FREQ_STATS.items()},
            "token_stats": {ctx: dict(counter) for ctx, counter in _TOKEN_STATS.items()},
            "recent_memory": {ctx: list(dq) for ctx, dq in _RECENT_MEMORY.items()},
            "config": {
                "recent_memory_maxlen": _RECENT_MEMORY_MAXLEN,
                "variation_resample_attempts": _VARIATION_RESAMPLE_ATTEMPTS,
                "bigram_overlap_threshold": _BIGRAM_OVERLAP_THRESHOLD,
                "freq_penalty_weight": _FREQ_PENALTY_WEIGHT,
                "rare_token_boost": _RARE_TOKEN_BOOST,
                "rare_token_threshold": _RARE_TOKEN_THRESHOLD,
            },
        }
        with open(STATS_STATE, "w", encoding="utf-8") as f:
            json.dump(stats_payload, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------


def learn_dialogue(context: str, line: str):
    if not USE_STRICT_CONDITIONAL:
        return
    hostile_model, neutral_model = _build_strict_models()
    if context == "hostility":
        hostile_model.add_line("hostility", line)
    else:
        sanitized = _sanitize_neutral_line(line)
        if not sanitized:
            return
        neutral_model.add_line(context, sanitized)
    _save_strict()


def extend_dialogue_corpus(context: str, lines: List[str]):
    if context not in DIALOGUE_CORPORA:
        DIALOGUE_CORPORA[context] = []
    for ln in lines:
        if context != "hostility":
            ln = _sanitize_neutral_line(ln)
        if not ln.strip():
            continue
        DIALOGUE_CORPORA[context].append(ln)
    # update live models if built
    if _STRICT_HOSTILE_MODEL and _STRICT_NEUTRAL_MODEL:
        if context == "hostility":
            for ln in lines:
                _STRICT_HOSTILE_MODEL.add_line("hostility", ln)
        else:
            for ln in lines:
                san = _sanitize_neutral_line(ln)
                if san:
                    _STRICT_NEUTRAL_MODEL.add_line(context, san)
        _save_strict()


def flush_dialogue_state():
    _save_strict()


# ---------------------------------------------------------------------------
# Stats snapshot API
# ---------------------------------------------------------------------------


def get_diversity_stats_snapshot() -> Dict[str, Dict[str, int]]:
    return {
        "freq_stats": {ctx: dict(counter) for ctx, counter in _FREQ_STATS.items()},
        "token_stats": {ctx: dict(counter) for ctx, counter in _TOKEN_STATS.items()},
        "recent_counts": {ctx: len(dq) for ctx, dq in _RECENT_MEMORY.items()},
    }


# ---------------------------------------------------------------------------
# Autoload diversity stats at import (without forcing model build)
# ---------------------------------------------------------------------------


def _autoload_diversity_stats():
    if not STRICT_PERSISTENCE:
        return
    if not os.path.exists(STATS_STATE):
        return
    try:
        with open(STATS_STATE, "r", encoding="utf-8") as f:
            data = json.load(f)
        _FREQ_STATS.clear()
        for ctx, mapping in data.get("freq_stats", {}).items():
            _FREQ_STATS[ctx] = Counter(mapping)
        _TOKEN_STATS.clear()
        for ctx, mapping in data.get("token_stats", {}).items():
            _TOKEN_STATS[ctx] = Counter(mapping)
        _RECENT_MEMORY.clear()
        for ctx, lines in data.get("recent_memory", {}).items():
            dq = deque(maxlen=_RECENT_MEMORY_MAXLEN)
            for ln in lines[-_RECENT_MEMORY_MAXLEN:]:
                dq.append(ln)
            _RECENT_MEMORY[ctx] = dq
    except Exception:
        pass


_autoload_diversity_stats()

# ---------------------------------------------------------------------------
# Generation with diversity controls
# ---------------------------------------------------------------------------


def _bigrams(tokens: List[str]):
    return set(zip(tokens, tokens[1:])) if len(tokens) > 1 else set()


def generate_markov_dialogue(
    context: str,
    trait: Optional[str] = None,
    seed: Optional[str] = None,
    adjusted_context: Optional[str] = None,
    tags: Optional[List[str]] = None,
    use_llm: bool = False,
) -> str:
    if not USE_STRICT_CONDITIONAL:
        return "..."
    hostile_model, neutral_model = _build_strict_models()
    ctx = context
    if trait == "aggressive" and ctx in ("encounter", "hostility"):
        ctx = "hostility"
    elif trait == "peaceful" and ctx in ("encounter", "hostility"):
        ctx = "idle"
    model = hostile_model if ctx == "hostility" else neutral_model

    hostile_set = set(_STYLE_LEXICON["hostility"]) | {"territory", "challenge", "dare"}
    max_words = 18

    # Generate base line
    base_tokens = model.generate(max_words=max_words)
    if ctx != "hostility":
        base_tokens = [t for t in base_tokens if t.lower() not in hostile_set]
        if not base_tokens:
            base_tokens = ["greetings"]
    recent = _RECENT_MEMORY[ctx]
    last_line = recent[-1] if recent else None

    def too_similar(tokens: List[str]) -> bool:
        if not last_line:
            return False
        lb = _bigrams(last_line.split()) if isinstance(last_line, str) else _bigrams(last_line)
        cb = _bigrams(tokens)
        if not lb or not cb:
            return False
        overlap = len(lb & cb) / max(1, len(lb))
        return overlap > _BIGRAM_OVERLAP_THRESHOLD

    line = " ".join(base_tokens)
    if not line.endswith((".", "!", "?")):
        line += "."

    # Frequency & similarity driven resampling
    def score(candidate: str) -> float:
        toks = candidate.split()
        line_freq = _FREQ_STATS[ctx][candidate]
        total_lines_ctx = sum(_FREQ_STATS[ctx].values()) or 1
        norm_line_freq = line_freq / total_lines_ctx
        rare_tokens = sum(1 for t in toks if _TOKEN_STATS[ctx][t] <= _RARE_TOKEN_THRESHOLD)
        rare_frac = rare_tokens / max(1, len(toks))
        return (rare_frac * _RARE_TOKEN_BOOST) - (norm_line_freq * _FREQ_PENALTY_WEIGHT)

    if (line in recent) or too_similar(line.split()):
        best_line = line
        best_score = score(line)
        attempts = 0
        while attempts < _VARIATION_RESAMPLE_ATTEMPTS:
            alt_tokens = model.generate(max_words=max_words)
            if ctx != "hostility":
                alt_tokens = [t for t in alt_tokens if t.lower() not in hostile_set]
                if not alt_tokens:
                    alt_tokens = ["greetings"]
            if too_similar(alt_tokens):
                attempts += 1
                continue
            cand = " ".join(alt_tokens)
            if not cand.endswith((".", "!", "?")):
                cand += "."
            if cand in recent:
                attempts += 1
                continue
            sc = score(cand)
            if sc > best_score:
                best_score = sc
                best_line = cand
            attempts += 1
        line = best_line

    # Update stats
    recent.append(line)
    _FREQ_STATS[ctx][line] += 1
    for tok in line.split():
        _TOKEN_STATS[ctx][tok] += 1

    # Optional LLM enhancement
    if use_llm:
        try:
            from gemini_narrative import enhance_markov_dialogue

            line = enhance_markov_dialogue(line, context)
        except ImportError:
            pass  # Fallback to Markov if LLM not available

    return line
