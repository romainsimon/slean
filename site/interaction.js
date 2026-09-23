document.addEventListener("DOMContentLoaded", () => {
  const french = document.documentElement.lang === "fr";
  const trigger = document.getElementById("toggle-toc-click");
  const toggle = document.getElementById("toggle-toc");
  const toc = document.getElementById("toc");
  if (trigger && toggle) {
    trigger.setAttribute("role", "button");
    trigger.setAttribute("tabindex", "0");
    trigger.setAttribute("aria-controls", "toc");
    const sync = () => {
      const open = toggle.checked;
      if (toc) toc.inert = window.matchMedia("(max-width: 700px)").matches && !open;
      trigger.setAttribute("aria-expanded", String(open));
      trigger.setAttribute("aria-label", open
        ? (french ? "Fermer le sommaire" : "Close table of contents")
        : (french ? "Ouvrir le sommaire" : "Open table of contents"));
    };
    trigger.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        toggle.checked = !toggle.checked;
        toggle.dispatchEvent(new Event("change", { bubbles: true }));
      }
    });
    toggle.addEventListener("change", sync);
    window.matchMedia("(max-width: 700px)").addEventListener("change", sync);
    sync();
  }

  document.querySelectorAll(".permalink-widget a").forEach((link) => {
    link.setAttribute("aria-label", french ? "Lien vers cette section" : "Link to this section");
  });
});
