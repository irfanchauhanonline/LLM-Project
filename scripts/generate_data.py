"""Generate a reproducible SYNTHETIC dataset of artists and songs.

This is demo data, not real music data. Each song is "written" from the
profile of one or two source artists (with noise and messy, inconsistent
tags, like real metadata). The source artists are the gold labels: the
artists an A&R person would agree are a suitable match.
"""
import json
import random
from pathlib import Path

random.seed(42)
OUT = Path(__file__).resolve().parent.parent / "data"

ARTISTS = [
    # id, name, genres, moods, tempo centre (BPM), vocal, lyric themes
    ("a01", "Nova Reign", ["pop", "dance pop"], ["euphoric", "confident"], 124, "female", ["party", "freedom", "night"]),
    ("a02", "The Hollow Pines", ["indie folk", "acoustic"], ["melancholic", "reflective"], 88, "male", ["home", "memory", "nature"]),
    ("a03", "Kairo Blaze", ["hip-hop", "trap"], ["aggressive", "confident"], 140, "male", ["hustle", "money", "city"]),
    ("a04", "Velvet Hours", ["r&b", "neo soul"], ["sensual", "smooth"], 92, "female", ["love", "desire", "night"]),
    ("a05", "Static Bloom", ["indie rock", "alt rock"], ["energetic", "restless"], 132, "male", ["youth", "escape", "city"]),
    ("a06", "Lena Marr", ["singer-songwriter", "acoustic"], ["tender", "reflective"], 76, "female", ["heartbreak", "memory", "love"]),
    ("a07", "Ironvale", ["metal", "hard rock"], ["aggressive", "dark"], 160, "male", ["struggle", "rage", "war"]),
    ("a08", "Solace Drift", ["electronic", "ambient"], ["calm", "dreamy"], 100, "none", ["space", "nature", "dream"]),
    ("a09", "Maya Oduya", ["afrobeats", "dancehall"], ["joyful", "sensual"], 104, "female", ["party", "love", "summer"]),
    ("a10", "Grey Atlas", ["country", "americana"], ["nostalgic", "warm"], 96, "male", ["home", "road", "family"]),
    ("a11", "Lumen Choir", ["gospel", "soul"], ["uplifting", "warm"], 84, "group", ["faith", "hope", "family"]),
    ("a12", "Pixel Saints", ["synthwave", "electronic"], ["nostalgic", "dreamy"], 110, "male", ["night", "city", "dream"]),
    ("a13", "Rue Delacroix", ["jazz", "neo soul"], ["smooth", "melancholic"], 82, "female", ["love", "night", "memory"]),
    ("a14", "Bassline Union", ["drum and bass", "electronic"], ["energetic", "euphoric"], 174, "none", ["night", "freedom", "party"]),
    ("a15", "Juno Hart", ["pop", "singer-songwriter"], ["tender", "hopeful"], 98, "female", ["love", "youth", "hope"]),
    ("a16", "Cold Harbour", ["post-punk", "indie rock"], ["dark", "restless"], 138, "male", ["city", "isolation", "escape"]),
    ("a17", "Siena Gold", ["latin pop", "reggaeton"], ["joyful", "sensual"], 96, "female", ["party", "desire", "summer"]),
    ("a18", "Old Mill Road", ["bluegrass", "country"], ["joyful", "nostalgic"], 120, "group", ["road", "home", "family"]),
    # Near-neighbours: artists that look alike on paper, which is what makes ranking hard.
    ("a19", "Cherry Static", ["pop", "electropop"], ["euphoric", "playful"], 118, "female", ["party", "youth", "night"]),
    ("a20", "Dre Malone", ["hip-hop", "boom bap"], ["confident", "reflective"], 92, "male", ["hustle", "city", "family"]),
    ("a21", "Amber Lowe", ["r&b", "pop"], ["sensual", "confident"], 100, "female", ["love", "desire", "party"]),
    ("a22", "Fen & Field", ["indie folk", "americana"], ["warm", "nostalgic"], 92, "group", ["home", "road", "nature"]),
    ("a23", "Night Transit", ["synthwave", "post-punk"], ["dark", "dreamy"], 120, "male", ["night", "city", "isolation"]),
    ("a24", "Ola Benson", ["afrobeats", "r&b"], ["joyful", "smooth"], 100, "male", ["love", "party", "summer"]),
]

# Messy real-world tag variants: the same genre written different ways.
TAG_VARIANTS = {
    "hip-hop": ["hip hop", "Hip-Hop", "hiphop", "rap"],
    "r&b": ["rnb", "R&B", "r and b", "rhythm and blues"],
    "drum and bass": ["dnb", "drum & bass", "drum n bass"],
    "singer-songwriter": ["singer songwriter", "Singer/Songwriter"],
    "electronic": ["electronica", "Electronic"],
    "indie rock": ["Indie Rock", "indie-rock"],
    "alt rock": ["alternative rock", "alt-rock"],
    "neo soul": ["neo-soul", "Neo Soul"],
    "latin pop": ["Latin Pop", "latin"],
    "afrobeats": ["afrobeat", "Afrobeats", "afro pop"],
    "post-punk": ["post punk", "Post-Punk"],
    "dance pop": ["dance-pop", "Dance Pop"],
    "pop": ["Pop", "POP"],
    "metal": ["heavy metal", "Metal"],
    "country": ["Country", "country music"],
}

# Lyric words linked to each theme (used to write synthetic lyric snippets).
THEME_WORDS = {
    "party": ["dance", "lights", "crowd", "tonight"], "freedom": ["free", "wings", "open", "fly"],
    "night": ["midnight", "moon", "dark", "stars"], "home": ["porch", "kitchen", "doorway", "hometown"],
    "memory": ["remember", "photograph", "yesterday", "old"], "nature": ["river", "pines", "rain", "mountain"],
    "hustle": ["grind", "work", "climb", "paper"], "money": ["cash", "stacks", "rich", "gold"],
    "city": ["streets", "traffic", "concrete", "subway"], "love": ["heart", "darling", "hold", "kiss"],
    "desire": ["want", "close", "skin", "burn"], "youth": ["young", "school", "summer", "reckless"],
    "escape": ["run", "away", "leave", "highway"], "heartbreak": ["tears", "goodbye", "broken", "alone"],
    "struggle": ["fight", "chains", "bleed", "rise"], "rage": ["scream", "fire", "fury", "break"],
    "war": ["battle", "soldier", "steel", "blood"], "space": ["orbit", "stars", "void", "planet"],
    "dream": ["sleep", "drift", "float", "dreaming"], "summer": ["sun", "beach", "heat", "island"],
    "road": ["highway", "truck", "miles", "dust"], "family": ["mama", "brother", "table", "blood"],
    "faith": ["pray", "lord", "glory", "grace"], "hope": ["light", "tomorrow", "believe", "rise"],
    "isolation": ["alone", "empty", "walls", "silence"],
}
FILLER = ["oh", "yeah", "the", "we", "and", "my", "you", "in", "this", "is"]


def messy(tag: str) -> str:
    if tag in TAG_VARIANTS and random.random() < 0.55:
        return random.choice(TAG_VARIANTS[tag])
    return tag


def make_song(idx: int, sources: list[tuple]) -> dict:
    genres, moods, themes = set(), set(), set()
    for a in sources:
        genres.update(random.sample(a[2], k=random.randint(1, 2)))
        if random.random() < 0.8:
            moods.update(random.sample(a[3], k=1))
        themes.update(random.sample(a[6], k=2))
    # Noise: a random extra mood/theme from anywhere, like real tagging.
    if random.random() < 0.5:
        moods.add(random.choice(random.choice(ARTISTS)[3]))
    if random.random() < 0.3:
        themes.add(random.choice(list(THEME_WORDS)))
    tempo = sum(a[4] for a in sources) / len(sources) + random.gauss(0, 9)
    # Beat trackers often report half or double the real tempo.
    if random.random() < 0.2:
        tempo = tempo / 2 if tempo > 110 else tempo * 2
    vocal = random.choice(sources)[5]
    words = []
    for t in themes:
        words += random.sample(THEME_WORDS[t], k=random.randint(0, 2))
    words += random.sample(FILLER, k=8)
    # Speech-to-text drops or garbles some words.
    words = [w if random.random() > 0.2 else w[:-1] for w in words if random.random() > 0.15]
    random.shuffle(words)
    genre_tags = sorted(messy(g) for g in genres)
    if random.random() < 0.25:  # a quarter of uploads arrive with no genre tag at all
        genre_tags = []
    if random.random() < 0.15:  # some are tagged with a broad parent genre only
        genre_tags = [random.choice(["pop", "rock", "electronic", "soul"])]
    return {
        "id": f"s{idx:03d}",
        "title": f"Demo Track {idx}",
        "genre_tags": genre_tags,
        "mood_tags": sorted(moods),
        "tempo_bpm": round(tempo),
        "vocal": vocal,
        "lyrics_excerpt": " ".join(words),
        "gold_artist_ids": sorted(a[0] for a in sources),
    }


def main() -> None:
    OUT.mkdir(exist_ok=True)
    artists = [
        {"id": a[0], "name": a[1], "genres": a[2], "moods": a[3],
         "tempo_bpm": a[4], "vocal": a[5], "lyric_themes": a[6]}
        for a in ARTISTS
    ]
    songs = []
    for i in range(1, 181):
        # ~70% songs fit one artist, ~30% sit between two similar-ish artists.
        if random.random() < 0.7:
            sources = [random.choice(ARTISTS)]
        else:
            first = random.choice(ARTISTS)
            shared = [a for a in ARTISTS if a is not first and
                      (set(a[2]) & set(first[2]) or set(a[3]) & set(first[3]))]
            sources = [first, random.choice(shared or ARTISTS)]
        songs.append(make_song(i, sources))
    # Fixed split: tune on dev, report on test (never tune on test).
    for s in songs:
        s["split"] = "dev" if int(s["id"][1:]) % 3 else "test"
    (OUT / "artists.json").write_text(json.dumps(artists, indent=2))
    (OUT / "songs.json").write_text(json.dumps(songs, indent=2))
    (OUT / "theme_lexicon.json").write_text(json.dumps(THEME_WORDS, indent=2))
    print(f"Wrote {len(artists)} artists and {len(songs)} songs to {OUT}")


if __name__ == "__main__":
    main()
