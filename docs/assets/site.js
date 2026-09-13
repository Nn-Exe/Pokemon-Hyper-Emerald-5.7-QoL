/* Hyper Emerald v5.7 guide — shared chrome: nav, TOC, search, theme */
(function () {
  "use strict";

  var NAV = [
    { title: "Start here", items: [
      ["index.html", "Overview"],
      ["getting-started.html", "Install & play"],
      ["features.html", "QoL features & controls"],
      ["mechanics.html", "Game mechanics"]
    ]},
    { title: "Walkthrough", items: [
      ["walkthrough-hoenn.html", "Hoenn: Littleroot to Champion"],
      ["walkthrough-postgame.html", "Post-game: Sinnoh & beyond"],
      ["walkthrough-lost-artifacts.html", "Lost Artifacts questline"]
    ]},
    { title: "Reference", items: [
      ["trainers.html", "Gym Leaders & bosses"],
      ["pokemon-locations.html", "Pokémon locations"],
      ["legendaries.html", "Legendary Pokémon"],
      ["items.html", "Mega Stones & key items"]
    ]},
    { title: "Help", items: [
      ["faq.html", "FAQ & known issues"],
      ["credits.html", "Credits & sources"]
    ]}
  ];

  var here = location.pathname.split("/").pop() || "index.html";

  // ---- theme ----
  var root = document.documentElement;
  try {
    var saved = localStorage.getItem("he-theme");
    if (saved === "dark" || saved === "light") root.setAttribute("data-theme", saved);
  } catch (e) {}
  function toggleTheme() {
    var cur = root.getAttribute("data-theme");
    var sysDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    var isDark = cur ? cur === "dark" : sysDark;
    var next = isDark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("he-theme", next); } catch (e) {}
  }

  // ---- header ----
  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) {
      if (k === "text") n.textContent = attrs[k];
      else if (k === "html") n.innerHTML = attrs[k];
      else n.setAttribute(k, attrs[k]);
    }
    (children || []).forEach(function (c) { n.appendChild(c); });
    return n;
  }

  var header = el("header", { "class": "topbar" }, [
    el("div", { "class": "topbar-inner" }, [
      el("button", { "class": "icon-btn nav-toggle", "aria-label": "Open navigation", "id": "nav-toggle", text: "☰" }),
      el("a", { "class": "brand", href: "index.html" }, [
        el("span", { "class": "mark", text: "HE" }),
        el("span", { text: "Hyper Emerald " }),
        el("span", { "class": "long", text: "Lost Artifacts " }),
        el("span", { "class": "ver", text: "v5.7 guide" })
      ]),
      el("div", { "class": "spacer" }),
      el("div", { "class": "search" }, [
        el("input", { type: "search", id: "site-search", placeholder: "Search the guide…", autocomplete: "off", "aria-label": "Search the guide" }),
        el("kbd", { text: "/" }),
        el("div", { "class": "search-results", id: "search-results", role: "listbox" })
      ]),
      el("button", { "class": "icon-btn", id: "theme-toggle", "aria-label": "Toggle dark mode", title: "Toggle dark mode", text: "◐" })
    ])
  ]);
  document.body.insertBefore(header, document.body.firstChild);

  // ---- sidenav ----
  var nav = el("nav", { "class": "sidenav", id: "sidenav", "aria-label": "Guide sections" });
  NAV.forEach(function (g) {
    var group = el("div", { "class": "group" }, [el("div", { "class": "group-title", text: g.title })]);
    g.items.forEach(function (it) {
      var a = el("a", { href: it[0], text: it[1] });
      if (it[0] === here) { a.className = "current"; a.setAttribute("aria-current", "page"); }
      group.appendChild(a);
    });
    nav.appendChild(group);
  });
  var shell = document.querySelector(".shell");
  if (shell) shell.insertBefore(nav, shell.firstChild);

  document.getElementById("nav-toggle").addEventListener("click", function () {
    nav.classList.toggle("open");
  });
  document.getElementById("theme-toggle").addEventListener("click", toggleTheme);

  // ---- headings: ids, anchors, TOC ----
  var main = document.querySelector("main.content");
  var heads = main ? main.querySelectorAll("h2, h3") : [];
  var used = {};
  function slug(s) {
    return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 60) || "s";
  }
  Array.prototype.forEach.call(heads, function (h) {
    if (!h.id) {
      var id = slug(h.textContent); var i = 2; var base = id;
      while (used[id] || document.getElementById(id)) { id = base + "-" + (i++); }
      h.id = id;
    }
    used[h.id] = true;
    if (!h.querySelector(".anchor")) {
      var a = el("a", { "class": "anchor", href: "#" + h.id, "aria-label": "Link to this section", text: "#" });
      h.appendChild(a);
    }
  });
  var tocRail = document.querySelector(".toc-rail");
  if (tocRail && heads.length > 2) {
    tocRail.appendChild(el("div", { "class": "toc-title", text: "On this page" }));
    var links = [];
    Array.prototype.forEach.call(heads, function (h) {
      var t = h.cloneNode(true); var an = t.querySelector(".anchor"); if (an) an.remove();
      var a = el("a", { href: "#" + h.id, text: t.textContent.trim(), "class": h.tagName === "H3" ? "lvl3" : "" });
      tocRail.appendChild(a); links.push([h, a]);
    });
    if ("IntersectionObserver" in window) {
      var current = null;
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            links.forEach(function (l) { l[1].classList.toggle("active", l[0] === e.target); });
          }
        });
      }, { rootMargin: "-60px 0px -70% 0px", threshold: 0 });
      links.forEach(function (l) { io.observe(l[0]); });
    }
  } else if (tocRail) {
    tocRail.remove();
  }

  // ---- footer ----
  var footer = el("footer", { "class": "site-footer" }, [
    el("div", { "class": "inner" }, [
      el("span", { html: "Unofficial fan guide for <em>Pokémon Hyper Emerald: Lost Artifacts v5.7</em> and the English + QoL patch. Not affiliated with Nintendo, Game Freak or the hack's authors." }),
      el("span", { html: "<a href=\"https://github.com/Nn-Exe/Pokemon-Hyper-Emerald-5.7-QoL\">Patch repository on GitHub</a>" })
    ])
  ]);
  document.body.appendChild(footer);

  // ---- search ----
  var input = document.getElementById("site-search");
  var results = document.getElementById("search-results");
  var index = null, loading = false, activeIdx = -1;

  function loadIndex(cb) {
    if (index) return cb();
    if (loading) return;
    loading = true;
    fetch("data/search.json").then(function (r) { return r.json(); }).then(function (j) {
      index = j; loading = false; cb();
    }).catch(function () { loading = false; index = []; cb(); });
  }
  function escapeHtml(s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c]; }); }
  function render(q) {
    results.innerHTML = "";
    activeIdx = -1;
    q = q.trim().toLowerCase();
    if (q.length < 2) return;
    var terms = q.split(/\s+/);
    var scored = [];
    index.forEach(function (d) {
      var hay = (d.title + " " + d.text).toLowerCase();
      var score = 0;
      for (var i = 0; i < terms.length; i++) {
        var t = terms[i];
        if (hay.indexOf(t) < 0) { score = 0; break; }
        score += d.title.toLowerCase().indexOf(t) >= 0 ? 5 : 1;
      }
      if (score) scored.push([score, d]);
    });
    scored.sort(function (a, b) { return b[0] - a[0]; });
    if (!scored.length) { results.appendChild(el("div", { "class": "r-empty", text: "No matches." })); return; }
    scored.slice(0, 12).forEach(function (s) {
      var d = s[1];
      var pos = d.text.toLowerCase().indexOf(terms[0]);
      var start = Math.max(0, pos - 50);
      var snip = (start > 0 ? "…" : "") + d.text.slice(start, start + 130) + (d.text.length > start + 130 ? "…" : "");
      var a = el("a", { href: d.url, role: "option" }, [
        el("div", { "class": "r-page", text: d.page }),
        el("div", { "class": "r-title", text: d.title }),
        el("div", { "class": "r-snip", html: escapeHtml(snip) })
      ]);
      results.appendChild(a);
    });
  }
  if (input) {
    input.addEventListener("input", function () { loadIndex(function () { render(input.value); }); });
    input.addEventListener("focus", function () { loadIndex(function () { render(input.value); }); });
    input.addEventListener("keydown", function (e) {
      var items = results.querySelectorAll("a");
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        if (!items.length) return;
        activeIdx = (activeIdx + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
        Array.prototype.forEach.call(items, function (it, i) { it.classList.toggle("active", i === activeIdx); });
        items[activeIdx].scrollIntoView({ block: "nearest" });
      } else if (e.key === "Enter") {
        if (activeIdx >= 0 && items[activeIdx]) location.href = items[activeIdx].getAttribute("href");
        else if (items.length) location.href = items[0].getAttribute("href");
      } else if (e.key === "Escape") {
        results.innerHTML = ""; input.blur();
      }
    });
    document.addEventListener("click", function (e) {
      if (!e.target.closest(".search")) results.innerHTML = "";
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement !== input && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName)) {
        e.preventDefault(); input.focus();
      }
    });
  }

  // ---- helpers for data pages ----
  window.HE = {
    el: el,
    escapeHtml: escapeHtml,
    fetchJSON: function (path) { return fetch(path).then(function (r) { if (!r.ok) throw new Error(path); return r.json(); }); },
    partyHtml: function (party) {
      var box = el("div", { "class": "party" });
      party.forEach(function (p) {
        var m = el("div", { "class": "mon" });
        var h = "<div class='name'><span>" + escapeHtml(p.species) + "</span><span class='lv'>Lv " + p.level + "</span></div>";
        if (p.item) h += "<div class='sub'>@ " + escapeHtml(p.item) + "</div>";
        if (p.moves && p.moves.length) h += "<div class='moves'>" + p.moves.map(escapeHtml).join(" · ") + "</div>";
        m.innerHTML = h; box.appendChild(m);
      });
      return box;
    }
  };

  // ---- inline trainer teams: <div class="team" data-trainer="265"></div> ----
  var slots = document.querySelectorAll("[data-trainer]");
  if (slots.length) {
    HE.fetchJSON("data/trainers.json").then(function (d) {
      var byId = {};
      d.groups.forEach(function (g) { g.trainers.forEach(function (t) { byId[t.id] = t; }); });
      Array.prototype.forEach.call(slots, function (s) {
        var t = byId[parseInt(s.getAttribute("data-trainer"), 10)];
        if (!t) { s.innerHTML = "<p class='src'>team not found in data/trainers.json</p>"; return; }
        var head = el("div", { "class": "team-head" });
        head.innerHTML = "<strong>" + escapeHtml((t.cls ? t.cls + " " : "") + t.name) + "</strong> <span class='src'>" +
          escapeHtml(t.variant + (t.double ? " · Double Battle" : "")) + "</span>";
        s.appendChild(head);
        if (t.party.length) s.appendChild(HE.partyHtml(t.party));
        if (t.tip) { var c = el("div", { "class": "callout plain" }); c.innerHTML = "<p>" + escapeHtml(t.tip) + "</p>"; s.appendChild(c); }
      });
    }).catch(function () {});
  }
})();
