"""AdSense skeleton. Opt-in by placing ads module in modules/ and configuring.
No live ad code here - only slots. Swap in actual publisher ID when approved."""

MODULE = {
    "kind": "slot",
    "slug": "ads",
    "name": "Ads Module",
    "desc": "AdSense slot placeholders (disabled by default)",
    "icon": "ad",
}

def slot_after():
    # Return empty by default - replace with slot HTML + AdSense script when ready.
    return ""
