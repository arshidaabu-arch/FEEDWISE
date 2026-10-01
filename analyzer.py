"""Transparent demo-only visual heuristic.

This is NOT a trained fungal classifier. It detects coarse colour/texture
signals that may resemble discolouration. Results must be treated as
unverified screening hints, never as proof of fungal contamination.
Replace analyze_image() with a validated trained model for real use.
"""
def analyze_image(path):
    try:
        import cv2
        import numpy as np
        image=cv2.imread(str(path))
        if image is None:
            return "Image could not be read", "Try a clear, well-lit JPG or PNG image."
        hsv=cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # Coarse demo cues: green/blue/very dark pixels plus local texture.
        h,s,v=cv2.split(hsv)
        unusual=((h>=35)&(h<=105)&(s>35)&(v>35)) | ((h>=90)&(h<=135)&(s>35)&(v>30))
        dark=(v<45)
        ratio=float((unusual|dark).mean())
        gray=cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        texture=float(gray.std())
        if ratio > 0.10 and texture > 28:
            return "Possible mould-like pattern", "Demo heuristic flagged unusual colour/texture. It cannot identify fungi or toxins; inspect and test the sample."
        return "No obvious mould-like pattern flagged", "The demo heuristic did not flag strong colour/texture cues. A negative result does not prove the feed is safe."
    except Exception as exc:
        return "Analysis unavailable", f"Image analysis could not run ({type(exc).__name__}). Check the installation and image."
