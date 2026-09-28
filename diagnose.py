"""
DON v3.0 — Gemini diagnostic.

Run this to find EXACTLY which model works with your key:
    python diagnose.py

It:
  1. Confirms your API key is loaded.
  2. Lists every model your key can see, with the actions each supports.
  3. Actually attempts a tiny real generateContent call on each candidate
     model (both with and without the 'models/' prefix) and reports which
     ones succeed — so we know the precise string to put in .env.
"""
from __future__ import annotations

import config


def main() -> None:
    print("=" * 60)
    print("  DON Gemini diagnostic")
    print("=" * 60)

    if not config.GEMINI_API_KEY:
        print("[!] No GEMINI_API_KEY found in .env. Add it and retry.")
        return
    print(f"API key loaded: ...{config.GEMINI_API_KEY[-6:]} (last 6 chars)")

    try:
        from google import genai
    except Exception as exc:
        print(f"[!] google-genai not installed ({exc}). Run: pip install google-genai")
        return

    client = genai.Client(api_key=config.GEMINI_API_KEY)

    # --- 1. List models ---
    print("\n--- Models your key can see ---")
    listed = []
    try:
        for m in client.models.list():
            name = getattr(m, "name", "")
            actions = (getattr(m, "supported_actions", None)
                       or getattr(m, "supported_generation_methods", None) or [])
            listed.append((name, actions))
            print(f"  {name}   actions={list(actions)}")
    except Exception as exc:
        print(f"[!] Could not list models: {exc}")

    # --- 2. Try a real call on candidate flash/pro text models ---
    print("\n--- Testing real generateContent calls ---")
    # Build candidate names (both with and without 'models/' prefix).
    candidates = []
    for name, actions in listed:
        short = name.split("/")[-1]
        if any(x in short for x in ("tts", "image", "audio", "vision", "embedding")):
            continue
        if "flash" in short or "pro" in short:
            candidates.append(short)
            candidates.append(name)  # full 'models/...'
    # De-dup preserving order.
    seen = set(); ordered = []
    for c in candidates:
        if c not in seen:
            seen.add(c); ordered.append(c)

    working = []
    for cand in ordered:
        try:
            resp = client.models.generate_content(
                model=cand, contents="Say OK."
            )
            txt = (getattr(resp, "text", "") or "").strip()
            print(f"  [WORKS]  {cand!r}  -> {txt[:30]!r}")
            working.append(cand)
        except Exception as exc:
            reason = str(exc).split("\n")[0][:80]
            print(f"  [fails]  {cand!r}  -> {reason}")

    print("\n" + "=" * 60)
    if working:
        print("SUCCESS. Put this line in your .env:")
        print(f"    DON_GEMINI_MODEL={working[0]}")
        print("(then run: python test_brain.py)")
    else:
        print("No model accepted a call. Copy this entire output and send it back.")
    print("=" * 60)


if __name__ == "__main__":
    main()
