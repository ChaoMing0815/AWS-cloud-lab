#!/usr/bin/env python3
"""Create deterministic, opaque redactions for report-only evidence copies."""

from pathlib import Path

from PIL import Image, ImageDraw


REPORT_DIR = Path(__file__).resolve().parents[1]
REPO_DOCS = REPORT_DIR.parents[1]
EVIDENCE_DIR = REPORT_DIR / "assets" / "evidence"
MASK_COLOR = (76, 201, 235, 255)


def redact(source: Path, destination: Path, boxes: tuple[tuple[int, int, int, int], ...]) -> None:
    image = Image.open(source).convert("RGBA")
    draw = ImageDraw.Draw(image)
    for box in boxes:
        draw.rectangle(box, fill=MASK_COLOR)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, optimize=True)


def main() -> None:
    redact(
        REPO_DOCS / "screenshots" / "phase0-tier0-private-db-route.png",
        EVIDENCE_DIR / "private-db-route-sanitized.png",
        ((40, 136, 245, 164),),
    )
    redact(
        REPO_DOCS / "screenshots" / "phase0-tier0-ssm-managed-node-online.png",
        EVIDENCE_DIR / "ssm-managed-node-sanitized.png",
        (
            (84, 216, 212, 254),
            (1388, 216, 1518, 254),
            (1538, 216, 1668, 254),
            (1708, 216, 1792, 254),
        ),
    )
    redact(
        EVIDENCE_DIR / "worker-asg-instances.png",
        EVIDENCE_DIR / "worker-asg-instances.png",
        ((88, 202, 213, 233), (88, 242, 213, 274)),
    )
    redact(
        EVIDENCE_DIR / "github-release-v1-1-6-summary.png",
        EVIDENCE_DIR / "github-release-v1-1-6-summary.png",
        ((395, 145, 620, 181), (396, 647, 815, 681), (390, 774, 466, 807)),
    )


if __name__ == "__main__":
    main()
