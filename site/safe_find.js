// This replaces Verso's inline xref handler after the two manuals are rendered.
// The generated xref data remains authoritative; URL parameters are plain text.
const french = document.documentElement.lang === "fr";
const labels = french
    ? {
          missingTitle: "Introuvable : ",
          missingHeading: "Nom introuvable : ",
          ambiguousTitle: "Ambigu : ",
          ambiguousHeading: "Nom ambigu : ",
          noName: "Aucun nom fourni",
          noNameHelp: "Cette page attend un paramètre « name » et des domaines de documentation.",
          domains: "Domaines consultés :",
          options: "Possibilités :",
          from: "Depuis ",
      }
    : {
          missingTitle: "Not found: ",
          missingHeading: "Not found: name ",
          ambiguousTitle: "Ambiguous: ",
          ambiguousHeading: "Ambiguous: name ",
          noName: "No name provided",
          noNameHelp: "This page expects a 'name' query parameter, along with documentation domains.",
          domains: "Searched domains:",
          options: "Options:",
          from: "From ",
      };

const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
const selectedDomains = domains.length
    ? domains.filter((domain) => own(xref, domain))
    : Object.keys(xref);
const options = [];
if (paramName) {
    for (const domain of selectedDomains) {
        const entries = xref[domain]?.contents?.[paramName];
        if (Array.isArray(entries)) {
            for (const entry of entries) options.push({ ...entry, domain });
        }
    }
}

function appendText(parent, tag, value) {
    const element = document.createElement(tag);
    element.textContent = value;
    parent.appendChild(element);
    return element;
}

function localXrefAddress(entry) {
    const address = new URL(String(entry.address).replace(/^\//, ""), document.baseURI);
    if (address.origin !== window.location.origin) return null;
    address.hash = String(entry.id);
    return address;
}

if (options.length === 1) {
    const address = localXrefAddress(options[0]);
    if (address) window.location.replace(address);
} else {
    addEventListener("DOMContentLoaded", () => {
        const title = document.querySelector("#title");
        const message = document.querySelector("#message");
        if (!paramName) {
            document.title = labels.noName;
            if (title) title.textContent = labels.noName;
            if (message) appendText(message, "p", labels.noNameHelp);
        } else if (options.length === 0) {
            document.title = labels.missingTitle + "'" + paramName + "'";
            if (title) title.textContent = labels.missingHeading + "'" + paramName + "'";
            if (message) {
                appendText(message, "p", labels.domains);
                const list = message.appendChild(document.createElement("ul"));
                for (const domain of selectedDomains) {
                    const item = list.appendChild(document.createElement("li"));
                    appendText(item, "code", domain);
                    item.appendChild(document.createTextNode(": " + (xref[domain].title || "")));
                }
            }
        } else {
            document.title = labels.ambiguousTitle + "'" + paramName + "'";
            if (title) title.textContent = labels.ambiguousHeading + "'" + paramName + "'";
            if (message) {
                appendText(message, "p", labels.options);
                const list = message.appendChild(document.createElement("ul"));
                for (const entry of options) {
                    const address = localXrefAddress(entry);
                    if (!address) continue;
                    const item = list.appendChild(document.createElement("li"));
                    const link = item.appendChild(document.createElement("a"));
                    link.href = address.href;
                    link.textContent = labels.from + (xref[entry.domain].title || "");
                }
            }
        }
    });
}
