import streamlit as st
from PIL import Image
import numpy as np
from datetime import datetime
import sqlite3, uuid, io
from pathlib import Path

BASE=Path(__file__).parent
DB=BASE/"smartfeed.db"
st.set_page_config(page_title="SmartFeed AI",page_icon="🐄",layout="wide")

def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS inspections(
        id INTEGER PRIMARY KEY AUTOINCREMENT, sample_id TEXT, created_at TEXT,
        feed_type TEXT, cattle_type TEXT, target_protein REAL, measured_protein REAL,
        moisture REAL, visual_result TEXT, visual_note TEXT, image BLOB)""")
init_db()

def analyze_image(img):
    """Demo-only colour heuristic, not a trained fungal classifier."""
    arr=np.asarray(img.convert("RGB")).astype(np.int16)
    r,g,b=arr[:,:,0],arr[:,:,1],arr[:,:,2]
    # Broad unusual green/blue/dark colour cues; lighting and feed type affect these.
    green_blue=((g>r*1.12)&(g>b*0.88)&(g>55)) | ((b>r*1.12)&(b>g*0.88)&(b>55))
    dark=(r<48)&(g<48)&(b<48)
    ratio=float(np.mean(green_blue|dark))
    if ratio>0.10:
        return "Possible mould-like pattern", f"Demo heuristic flagged unusual colour cues ({ratio*100:.1f}% of pixels). This is not proof of mould."
    return "No obvious mould-like pattern flagged", f"No strong colour cue was flagged ({ratio*100:.1f}% of pixels). This does not prove the feed is safe."

def save(item):
    with sqlite3.connect(DB) as c:
        c.execute("""INSERT INTO inspections(sample_id,created_at,feed_type,cattle_type,target_protein,
        measured_protein,moisture,visual_result,visual_note,image) VALUES(?,?,?,?,?,?,?,?,?,?)""",
        (item["sample_id"],item["created_at"],item["feed_type"],item["cattle_type"],
         item["target"],item["measured"],item["moisture"],item["visual"],item["note"],item["image"]))

def get_history():
    with sqlite3.connect(DB) as c:
        c.row_factory=sqlite3.Row
        return c.execute("SELECT * FROM inspections ORDER BY id DESC").fetchall()

st.markdown("""
<style>
.stApp{background:#f5f8f6;color:#17251e}
.block-container{max-width:1200px;padding-top:2rem}
.hero{background:linear-gradient(110deg,#e5f4e9,#f6fbf7);padding:24px 30px;border:1px solid #d6e9dc;border-radius:18px;margin-bottom:18px}
.hero h1{color:#075c3c;font-size:2.25rem;margin:0}
.hero p{color:#4c6255;margin:.4rem 0 0}
div[data-testid="stMetric"]{background:white;border:1px solid #e1e9e3;padding:12px;border-radius:12px}
.warning{background:#fff4dc;border:1px solid #efd9a4;border-radius:10px;padding:12px;color:#79591d}
.good{background:#eaf6ee;border:1px solid #d2e8d9;border-radius:10px;padding:12px;color:#17613e}
</style>
""",unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>🐄 SmartFeed AI</h1><p>AI-assisted cattle feed inspection and nutritional assessment · SIH prototype</p></div>',unsafe_allow_html=True)
st.markdown('<div class="warning"><b>Prototype limitation:</b> visual screening below is a simple demo heuristic, not a validated fungal detector. Protein and moisture are user-entered values, not camera measurements. Do not use this app to certify feed safety.</div>',unsafe_allow_html=True)
tab1,tab2,tab3=st.tabs(["🧪 New inspection","📋 Inspection history","ℹ️ About & limitations"])
with tab1:
    left,right=st.columns([1.05,1])
    with left:
        st.subheader("1. Sample details")
        feed=st.selectbox("Feed type",["Maize","Wheat bran","Rice bran","Groundnut cake","Soybean meal","Green fodder","Dry fodder","Silage","Commercial cattle feed","Other"])
        cattle=st.selectbox("Cattle category",["Calf","Growing cattle","Adult maintenance","Lactating cow","Pregnant cow","Bull"])
        target=st.number_input("Target crude protein (%)",min_value=0.0,max_value=100.0,value=16.0,step=0.5)
        measured=st.number_input("Measured crude protein (%) — from lab/NIR",min_value=0.0,max_value=100.0,value=0.0,step=0.1,help="Enter 0 if not measured; leave checkbox off below.")
        has_protein=st.checkbox("I have a measured protein value",value=False)
        moisture=st.number_input("Measured moisture (%) — from meter",min_value=0.0,max_value=100.0,value=0.0,step=0.1)
        has_moisture=st.checkbox("I have a measured moisture value",value=False)
    with right:
        st.subheader("2. Capture or upload sample")
        uploaded=st.file_uploader("Upload a feed image",type=["png","jpg","jpeg","webp"])
        camera=st.camera_input("Or take a photo with your camera")
        img=None
        if camera:
            img=Image.open(camera)
        elif uploaded:
            img=Image.open(uploaded)
        if img:
            st.image(img,caption="Selected feed sample",use_container_width=True)
    if st.button("🔍 Analyze sample",type="primary",use_container_width=True):
        if img is None:
            st.error("Please capture or upload a feed image before analysis.")
        else:
            visual,note=analyze_image(img)
            image_bytes=io.BytesIO()
            img.save(image_bytes,format="JPEG",quality=88)
            item={"sample_id":"SF-"+datetime.now().strftime("%y%m%d")+"-"+uuid.uuid4().hex[:6].upper(),
                  "created_at":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  "feed_type":feed,"cattle_type":cattle,"target":float(target) if target else None,
                  "measured":float(measured) if has_protein else None,
                  "moisture":float(moisture) if has_moisture else None,
                  "visual":visual,"note":note,"image":image_bytes.getvalue()}
            save(item)
            st.session_state["last_result"]=item
            st.success("Inspection saved.")
    if "last_result" in st.session_state:
        item=st.session_state["last_result"]
        st.divider()
        st.subheader("3. Analysis results")
        a,b=st.columns(2)
        with a:
            if "Possible" in item["visual"]:
                st.error("⚠️ "+item["visual"])
            else:
                st.info("🔎 "+item["visual"])
            st.caption(item["note"])
        with b:
            st.metric("Sample ID",item["sample_id"])
            st.metric("Feed",item["feed_type"])
        m1,m2,m3=st.columns(3)
        m1.metric("Target protein",f'{item["target"]:.1f}%' if item["target"] is not None else "—")
        m2.metric("Measured protein",f'{item["measured"]:.1f}%' if item["measured"] is not None else "Not entered")
        m3.metric("Moisture",f'{item["moisture"]:.1f}%' if item["moisture"] is not None else "Not entered")
        st.subheader("Recommendations")
        if "Possible" in item["visual"]:
            st.warning("Isolate the sample and arrange an appropriate laboratory assessment before feeding.")
        else:
            st.info("No strong visual cue was flagged. This is not confirmation that the feed is safe.")
        if item["measured"] is not None and item["target"] is not None:
            if item["measured"]<item["target"]:
                st.warning(f"Measured protein is {item['target']-item['measured']:.1f} percentage points below the entered target. Review the ration with a qualified nutritionist.")
            else:
                st.success("Measured protein meets or exceeds the entered target; verify the measurement and ration suitability.")
        else:
            st.info("Use a suitable laboratory or calibrated NIR test to obtain protein content.")
        if item["moisture"] is not None:
            st.write("Compare moisture with the specification for this feed and its storage method. The app does not apply a universal moisture limit.")
        st.caption("Mycotoxins cannot be detected by this image screen. Use validated tests such as appropriate ELISA or laboratory analysis.")
with tab2:
    st.subheader("Saved inspections")
    rows=get_history()
    if rows:
        for row in rows:
            with st.expander(f'{row["sample_id"]} · {row["feed_type"]} · {row["created_at"]}'):
                c1,c2=st.columns([1,2])
                with c1:
                    if row["image"]: st.image(row["image"],use_container_width=True)
                with c2:
                    st.write("**Cattle category:**",row["cattle_type"])
                    st.write("**Visual screen:**",row["visual_result"])
                    st.write("**Protein:**",f'{row["measured_protein"]}%' if row["measured_protein"] is not None else "Not entered")
                    st.write("**Moisture:**",f'{row["moisture"]}%' if row["moisture"] is not None else "Not entered")
                    st.caption(row["visual_note"])
        if st.button("Clear all history"):
            with sqlite3.connect(DB) as c:c.execute("DELETE FROM inspections")
            st.rerun()
    else:
        st.info("No inspections saved yet. Run a new inspection to populate history.")
with tab3:
    st.subheader("About this prototype")
    st.markdown("""
- **Image screening:** colour-based demo heuristic only. Replace it with a trained, independently validated model before claiming AI fungal detection.
- **Protein:** user-entered laboratory/NIR value; a normal RGB camera cannot measure crude protein.
- **Moisture:** user-entered meter reading; no sensor is connected in this software demo.
- **Mycotoxins:** cannot be identified or quantified from an ordinary image.
- **Recommendations:** informational prompts, not a veterinary ration formulation or feed-safety certification.
""")
st.caption("SmartFeed AI · SIH demonstration prototype · Local SQLite history")
