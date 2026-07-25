"""Offline 'sample' LMS content connector for the public demo.

Serves a small set of real, self-contained study-note files entirely from memory, so the
one-click "Import course files from your LMS" flow works end-to-end in the hosted demo
without any external LMS, network call, or token. Real institutions connect
canvas / moodle / brightspace instead; those providers return the same normalized shape:

    list_course_files(base_url, token, course_ref) -> [{id, name, content_type, download_url}]
    download_file(download_url, token, *, max_bytes) -> bytes
"""
from __future__ import annotations

# course_ref -> [(filename, markdown body), ...]. Content mirrors each demo course's early
# concepts so the imported material genuinely grounds the AI tutor's remediation.
_FILES: dict[str, list[tuple[str, str]]] = {
    "BS-CS201": [
        (
            "Binary representation — study notes.md",
            "# Binary representation\n\n"
            "A binary number is a sum of powers of two. Read it right-to-left; the column "
            "values are 1, 2, 4, 8, 16, ...\n\n"
            "**Example.** `1011` = 1·8 + 0·4 + 1·2 + 1·1 = **11**.\n\n"
            "## Common mistakes\n"
            "- Counting the number of 1-bits instead of summing place values.\n"
            "- Reading the bits as base-10 digits (thinking `1011` is one thousand eleven).\n\n"
            "## How many values fit in n bits?\n"
            "`n` bits represent **2^n** distinct values (not 2·n). So 4 bits give 16 values, "
            "from 0000 (0) to 1111 (15) — and remember that 0 is one of them.\n",
        ),
        (
            "Two's complement cheat sheet.md",
            "# Two's complement (signed integers)\n\n"
            "To encode a negative number in `n` bits: **invert every bit, then add 1**.\n\n"
            "**Example (-3 in 4 bits).** +3 = `0011` -> invert -> `1100` -> add 1 -> **`1101`**.\n\n"
            "## Watch out\n"
            "- Inverting the bits but forgetting the +1 is the most common error.\n"
            "- The most significant bit is the sign bit: 1 means negative.\n"
            "- Fixed width wraps around. In 8 bits, `0xFF` + 1 = `0x00` with a carry/overflow — "
            "registers do not grow.\n",
        ),
    ],
    "BS-CS310": [
        (
            "Inheritance and dynamic dispatch.md",
            "# Inheritance & dynamic dispatch\n\n"
            "When a subclass overrides a method, the method that runs is chosen by the "
            "**actual object's type at runtime**, not the declared reference type.\n\n"
            "```\nBase b = new Derived();\nb.speak();   // runs Derived.speak(), not Base.speak()\n```\n\n"
            "This is *dynamic dispatch*. The declared type (`Base`) only decides which methods "
            "are visible to the compiler; the object (`Derived`) decides which override executes.\n\n"
            "## Encapsulation reminder\n"
            "Make fields private and expose getters/setters to **control and validate access** to "
            "internal state — not for speed or memory reasons.\n",
        ),
        (
            "Polymorphism in practice.md",
            "# Polymorphism\n\n"
            "A collection of base-type references can hold different subclass objects, and calling "
            "the same method on each runs that subclass's own implementation.\n\n"
            "```\nList<Shape> shapes = [new Circle(), new Square()];\nfor (Shape s : shapes)\n"
            "    s.area();   // Circle.area() then Square.area()\n```\n\n"
            "Each object is substitutable for its base type (Liskov substitution). Expecting "
            "`Shape.area()` to run for every element is the classic misconception.\n",
        ),
    ],
    "BS-DS200": [
        (
            "Conditional probability primer.md",
            "# Conditional probability\n\n"
            "`P(A | B) = P(A ∩ B) / P(B)` — the joint probability divided by the probability of "
            "the condition.\n\n"
            "**Example.** P(A∩B)=0.2, P(B)=0.5 -> P(A|B) = 0.2 / 0.5 = **0.4**.\n\n"
            "## Common errors\n"
            "- Reporting the joint probability (0.2) and forgetting to divide by P(B).\n"
            "- Adding probabilities instead of conditioning.\n",
        ),
        (
            "Distributions quick reference.md",
            "# Distributions quick reference\n\n"
            "**Binomial(n, p).** Number of successes in `n` independent trials.\n"
            "Expected value `E[X] = n·p` (not just `p`, and not `n`).\n\n"
            "**Example.** X ~ Binomial(n=10, p=0.5) -> E[X] = 10·0.5 = **5**.\n\n"
            "## Hypothesis testing note\n"
            "A p-value of 0.03 at α=0.05 means 0.03 < 0.05, so you **reject the null**. The "
            "p-value is *not* the probability that the null hypothesis is true.\n",
        ),
    ],
}


def _lookup(course_ref: str | None) -> list[tuple[str, str]]:
    ref = (course_ref or "").strip()
    return _FILES.get(ref) or _FILES.get(ref.upper()) or []


def list_course_files(
    base_url: str, token: str, course_ref: str, *, limit: int = 500
) -> list[dict]:
    files = _lookup(course_ref)[:limit]
    return [
        {
            "id": f"sample-{i}",
            "name": name,
            "content_type": "text/markdown",
            "download_url": f"sample://{course_ref}/{i}",
        }
        for i, (name, _body) in enumerate(files)
    ]


def download_file(download_url: str, token: str, *, max_bytes: int | None = None) -> bytes:
    # download_url = sample://<course_ref>/<index>
    rest = download_url.split("://", 1)[-1]
    course_ref, _, idx = rest.rpartition("/")
    files = _lookup(course_ref)
    _name, body = files[int(idx)]
    data = body.encode("utf-8")
    if max_bytes is not None and len(data) > max_bytes:
        data = data[:max_bytes]
    return data
