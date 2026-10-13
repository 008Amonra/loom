/* 45dgof8 site i18n engine
 * Default language: English (the content in the HTML).
 * German is applied at runtime from assets/i18n.de.js.
 * One shared engine, injected toggle, no external services, no tracking.
 * Usage on a page:  <script src="assets/i18n.de.js" defer></script>
 *                   <script src="assets/i18n.js" defer></script>
 */
(function () {
  "use strict";

  var LANG_KEY = "site-lang";
  var dict = window.I18N_DE || {};
  var meta = dict.meta || {};
  var pages = dict.pages || {};
  var navMap = dict.nav || {};

  var ATTRS = ["placeholder", "title", "aria-label", "alt"];

  function pageKey() {
    var p = location.pathname.split("/").pop();
    return p === "" || p === undefined ? "index.html" : p;
  }

  var current = Object.assign({}, navMap, pages[pageKey()] || {});
  var hasPage = Object.prototype.hasOwnProperty.call(pages, pageKey());

  var textNodes = [];
  var attrNodes = [];
  var origTitle = document.title;
  var descEl = document.querySelector('meta[name="description"]');
  var origDesc = descEl ? descEl.getAttribute("content") : null;

  function isSkippable(node) {
    var p = node.parentNode;
    while (p && p.nodeType === 1) {
      var tag = p.nodeName;
      if (tag === "SCRIPT" || tag === "STYLE" || tag === "NOSCRIPT" || tag === "CODE" || tag === "PRE") return true;
      if (p.classList && p.classList.contains("i18n-skip")) return true;
      p = p.parentNode;
    }
    return false;
  }

  function capture() {
    var w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
    var n;
    while ((n = w.nextNode())) {
      if (isSkippable(n)) continue;
      if (!n.nodeValue || !n.nodeValue.trim()) continue;
      textNodes.push({ node: n, en: n.nodeValue });
    }
    var els = document.querySelectorAll("[placeholder],[title],[aria-label],[alt]");
    for (var i = 0; i < els.length; i++) {
      for (var j = 0; j < ATTRS.length; j++) {
        var a = ATTRS[j];
        if (!els[i].hasAttribute(a)) continue;
        var v = els[i].getAttribute(a);
        if (!v || !v.trim()) continue;
        attrNodes.push({ el: els[i], attr: a, en: v });
      }
    }
  }

  function normKey(s) {
    return s.replace(/\s+/g, " ").trim();
  }

  var normCurrent = {};
  for (var nk in current) {
    if (Object.prototype.hasOwnProperty.call(current, nk)) normCurrent[normKey(nk)] = current[nk];
  }

  function translatedValue(raw) {
    var key = normKey(raw);
    if (!Object.prototype.hasOwnProperty.call(normCurrent, key)) return null;
    var lead = raw.match(/^\s*/)[0];
    var trail = raw.match(/\s*$/)[0];
    return lead + normCurrent[key] + trail;
  }

  function applyDeText() {
    for (var i = 0; i < textNodes.length; i++) {
      var it = textNodes[i];
      var t = translatedValue(it.en);
      it.node.nodeValue = t === null ? it.en : t;
    }
    for (var j = 0; j < attrNodes.length; j++) {
      var at = attrNodes[j];
      var tv = translatedValue(at.en);
      at.el.setAttribute(at.attr, tv === null ? at.en : tv);
    }
  }

  function applyEnText() {
    for (var i = 0; i < textNodes.length; i++) textNodes[i].node.nodeValue = textNodes[i].en;
    for (var j = 0; j < attrNodes.length; j++) attrNodes[j].el.setAttribute(attrNodes[j].attr, attrNodes[j].en);
  }

  function applyMeta(lang) {
    var pk = pageKey();
    var m = meta[pk] && meta[pk][lang];
    if (lang === "de" && m) {
      if (m.title) document.title = m.title;
      if (m.desc && descEl) descEl.setAttribute("content", m.desc);
    } else {
      document.title = origTitle;
      if (descEl && origDesc !== null) descEl.setAttribute("content", origDesc);
    }
  }

  var toggle = null;
  var segEn = null;
  var segDe = null;

  function styleToggle() {
    if (document.getElementById("site-lang-style")) return;
    var s = document.createElement("style");
    s.id = "site-lang-style";
    s.textContent =
      ".site-lang{display:inline-flex;align-items:center;gap:3px;font-family:'JetBrains Mono',ui-monospace,monospace;" +
      "font-size:0.72rem;letter-spacing:2px;background:rgba(13,13,20,.85);border:1px solid #3a3a4e;border-radius:20px;" +
      "padding:3px;cursor:pointer;transition:.2s;z-index:9999}" +
      ".site-lang:hover{border-color:#00ff88}" +
      ".site-lang span{padding:4px 10px;border-radius:16px;color:#666;transition:.2s;user-select:none}" +
      ".site-lang span.active{background:rgba(0,255,136,.12);color:#00ff88;border:1px solid rgba(0,255,136,.35);padding:4px 9px}" +
      ".site-lang.float{position:fixed;top:14px;right:14px;box-shadow:0 4px 18px rgba(0,0,0,.4)}";
    document.head.appendChild(s);
  }

  function buildToggle() {
    styleToggle();
    toggle = document.createElement("div");
    toggle.className = "site-lang";
    toggle.setAttribute("role", "group");
    toggle.setAttribute("aria-label", "Language / Sprache");
    segEn = document.createElement("span");
    segEn.textContent = "EN";
    segEn.setAttribute("data-lang", "en");
    segDe = document.createElement("span");
    segDe.textContent = "DE";
    segDe.setAttribute("data-lang", "de");
    toggle.appendChild(segEn);
    toggle.appendChild(segDe);

    var nav = document.querySelector("nav");
    if (nav) {
      var host = nav.querySelector(".nav-links") || nav.querySelector(".nav-right") || nav;
      if (host.classList && host.classList.contains("nav-links")) {
        host.parentNode.appendChild(toggle);
      } else {
        host.appendChild(toggle);
      }
    } else {
      toggle.classList.add("float");
      document.body.appendChild(toggle);
    }

    toggle.addEventListener("click", function (e) {
      var sp = e.target.closest ? e.target.closest("span[data-lang]") : null;
      var lang = sp ? sp.getAttribute("data-lang") : (getLang() === "en" ? "de" : "en");
      setLang(lang);
    });
  }

  function markToggle(lang) {
    if (!segEn) return;
    segEn.classList.toggle("active", lang === "en");
    segDe.classList.toggle("active", lang === "de");
  }

  function getLang() {
    var cur = document.documentElement.getAttribute("lang");
    return cur === "de" ? "de" : "en";
  }

  function setLang(lang) {
    if (lang !== "de") lang = "en";
    document.documentElement.setAttribute("lang", lang);
    if (lang === "de") applyDeText(); else applyEnText();
    applyMeta(lang);
    markToggle(lang);
    try { localStorage.setItem(LANG_KEY, lang); } catch (e) {}
  }

  function init() {
    if (!hasPage) return;                 // page not translated yet: engine stays quiet
    capture();
    buildToggle();
    var saved = "en";
    try { saved = localStorage.getItem(LANG_KEY) || "en"; } catch (e) {}
    setLang(saved === "de" ? "de" : "en");
  }

  window.setSiteLang = setLang;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
