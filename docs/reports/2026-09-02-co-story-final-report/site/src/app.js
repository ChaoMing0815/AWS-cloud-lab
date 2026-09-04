const sections = [...document.querySelectorAll("[data-capture]")];
const navLinks = [...document.querySelectorAll(".rail a")];
const progress = document.querySelector("#rail-progress");
const query = new URLSearchParams(location.search);
const captureMode = query.get("capture") === "1";
const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)").matches || query.get("reduced") === "1";

if (captureMode) {
  document.body.classList.add("capture-mode");
  document.documentElement.style.scrollBehavior = "auto";
}
if (reducedMotion) {
  document.body.classList.add("force-reduced-motion");
  document.documentElement.style.scrollBehavior = "auto";
}

function activateSection(index) {
  const safeIndex = Math.max(0, Math.min(index, sections.length - 1));
  sections.forEach((section, sectionIndex) => section.classList.toggle("is-active", sectionIndex === safeIndex));
  navLinks.forEach((link, linkIndex) => {
    if (linkIndex === safeIndex) link.setAttribute("aria-current", "true");
    else link.removeAttribute("aria-current");
  });
  progress.style.height = `${((safeIndex + 1) / sections.length) * 100}%`;
  if (!captureMode) history.replaceState(null, "", `${location.pathname}${location.search}#${sections[safeIndex].id}`);
}

const observer = new IntersectionObserver(
  (entries) => {
    const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
    if (visible) activateSection(sections.indexOf(visible.target));
  },
  { threshold: [0.45, 0.7] },
);
if (!captureMode) sections.forEach((section) => observer.observe(section));

document.addEventListener("keydown", (event) => {
  const current = sections.findIndex((section) => section.classList.contains("is-active"));
  const keyMap = { ArrowDown: 1, PageDown: 1, ArrowUp: -1, PageUp: -1 };
  if (event.key in keyMap) {
    event.preventDefault();
    sections[Math.max(0, Math.min(current + keyMap[event.key], sections.length - 1))].scrollIntoView({ behavior: "instant" });
  } else if (event.key === "Home") {
    event.preventDefault();
    sections[0].scrollIntoView({ behavior: "instant" });
  } else if (event.key === "End") {
    event.preventDefault();
    sections.at(-1).scrollIntoView({ behavior: "instant" });
  }
});

const requestedSection = Math.max(0, sections.findIndex((section) => `#${section.id}` === location.hash));
activateSection(requestedSection);
if (location.hash || captureMode) requestAnimationFrame(() => sections[requestedSection].scrollIntoView({ behavior: "auto" }));

addEventListener("hashchange", () => {
  const hashIndex = sections.findIndex((section) => `#${section.id}` === location.hash);
  if (hashIndex >= 0) activateSection(hashIndex);
});

document.documentElement.classList.add("js-enhanced");
