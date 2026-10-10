"""Privacy policy content module."""

MODULE = {
    "kind": "page",
    "slug": "privacy",
    "name": "Privacy Policy",
    "title": "Privacy Policy",
    "subtitle": "45dgof8 Tools",
    "meta_desc": "Privacy policy for 45dgof8 Tools - what we collect (nothing), ads, and your rights.",
    "icon": "lock",
}

def page():
    return r"""<div class="card">
<h2>Privacy Policy</h2>
<p class="mut">Last updated: 2026-10-10</p>
<h3 style="color:#c8a87c;margin:14px 0 8px">What we collect</h3>
<p class="mut">Most tools run entirely in your browser. Files you upload are processed locally or sent to our server only to perform the requested operation, then returned to you. We do not store your original files or results.</p>
<h3 style="color:#c8a87c;margin:14px 0 8px">Third-party services</h3>
<p class="mut">Open-Meteo (weather) and geocoding are used for weather lookups - requests go directly from your browser to those services where applicable. If we enable Google AdSense in future, Google will use cookies and device identifiers in accordance with its policies. We will update this page before enabling ads.</p>
<h3 style="color:#c8a87c;margin:14px 0 8px">Consent</h3>
<p class="mut">If AdSense is enabled, visitors in EEA/UK/CH must be given a consent choice (IAB TCF v2.2) via Google's Privacy & messaging in AdSense, or an equivalent consent management platform. The orb and purely client-side tools remain functional without consent.</p>
<p class="mut">By using these tools, you agree to this privacy policy.</p>
</div>"""
