"""
Ads Manager — Full ad creation, editing, preview, and performance tracking.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

from src.meta_api import MetaAPIManager
from src.helpers import format_currency, safe_float, safe_int
from src.meta_catalog import AD_STATUSES

st.set_page_config(page_title="Ads", page_icon="📢", layout="wide")

st.markdown("""<style>
    .stApp { font-family: 'Segoe UI', sans-serif; }
    .section-title { font-size: 1.3rem; font-weight: 600; color: #0078D4; margin: 16px 0 8px; }
    .ad-preview { background: #f5f5f5; border-radius: 12px; padding: 16px; margin: 8px 0;
        border: 1px solid #ddd; max-width: 500px; }
    .creative-thumb { border-radius: 8px; max-width: 200px; }
</style>""", unsafe_allow_html=True)


def get_api():
    return MetaAPIManager(
        st.session_state.get("access_token", ""),
        st.session_state.get("ad_account_id", ""),
    )


if not st.session_state.get("connected", False):
    st.warning("Connect to Meta API first from the main dashboard.")
    st.stop()

st.markdown("# Ads Manager")
api = get_api()

AD_FORMATS = [
    "DESKTOP_FEED_STANDARD", "MOBILE_FEED_STANDARD", "MOBILE_FEED_BASIC",
    "MOBILE_INTERSTITIAL", "MOBILE_BANNER", "RIGHT_COLUMN_STANDARD",
    "INSTAGRAM_STANDARD", "INSTAGRAM_STORY", "AUDIENCE_NETWORK_OUTSTREAM_VIDEO",
    "FACEBOOK_STORY_MOBILE", "MESSENGER_MOBILE_INBOX_MEDIA",
]

tab_list, tab_create, tab_preview, tab_creative = st.tabs([
    "All Ads", "Create Ad", "Ad Preview", "Creative Library",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1: ALL ADS
# ═══════════════════════════════════════════════════════════════════════════════

with tab_list:
    st.markdown('<div class="section-title">All Ads</div>', unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
    with col_f1:
        adset_filter = st.text_input("Filter by Ad Set ID", key="ad_adset_filter")
    with col_f2:
        ad_status_filter = st.multiselect("Status", AD_STATUSES, default=["ACTIVE", "PAUSED"], key="ad_status")
    with col_f3:
        st.write("")
        st.write("")
        st.button("Refresh", use_container_width=True, key="ad_refresh")

    try:
        with st.spinner("Loading ads..."):
            ads = api.get_ads(
                adset_id=adset_filter if adset_filter else None,
                status_filter=ad_status_filter if ad_status_filter else None,
            )

        if ads:
            rows = []
            for ad in ads:
                creative = ad.get("creative", {})
                rows.append({
                    "ID": ad.get("id", ""),
                    "Name": ad.get("name", ""),
                    "Status": ad.get("effective_status", ad.get("status", "")),
                    "Ad Set ID": ad.get("adset_id", ""),
                    "Campaign ID": ad.get("campaign_id", ""),
                    "Creative ID": creative.get("id", "") if isinstance(creative, dict) else "",
                    "Creative Name": creative.get("name", "") if isinstance(creative, dict) else "",
                    "Created": (ad.get("created_time") or "")[:10],
                })

            df = pd.DataFrame(rows)

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Ads", len(df))
            c2.metric("Active", len(df[df["Status"] == "ACTIVE"]))
            c3.metric("Paused", len(df[df["Status"] == "PAUSED"]))

            st.dataframe(df, use_container_width=True, hide_index=True, height=400)

            # Inline actions
            st.markdown("---")
            selected_ads = st.multiselect(
                "Select ads for action",
                options=[a["id"] for a in ads],
                format_func=lambda x: next(
                    (f"{a.get('name', '')} ({a['id']})" for a in ads if a["id"] == x), x
                ),
                key="ad_action_select",
            )

            if selected_ads:
                col_a1, col_a2, col_a3 = st.columns(3)
                with col_a1:
                    if st.button("Activate", type="primary", use_container_width=True, key="ad_activate"):
                        results = api.batch_update_status(selected_ads, "ACTIVE")
                        for r in results:
                            st.write(f"{r['id']}: {r['status']}")
                with col_a2:
                    if st.button("Pause", use_container_width=True, key="ad_pause"):
                        results = api.batch_update_status(selected_ads, "PAUSED")
                        for r in results:
                            st.write(f"{r['id']}: {r['status']}")
                with col_a3:
                    if st.button("Delete", use_container_width=True, key="ad_delete"):
                        for aid in selected_ads:
                            try:
                                api.delete_ad(aid)
                                st.warning(f"Deleted {aid}")
                            except Exception as e:
                                st.error(f"Failed {aid}: {e}")
        else:
            st.info("No ads found.")
    except Exception as e:
        st.error(f"Failed to load ads: {str(e)[:300]}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2: CREATE AD
# ═══════════════════════════════════════════════════════════════════════════════

with tab_create:
    st.markdown('<div class="section-title">Create New Ad</div>', unsafe_allow_html=True)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        ad_adset_id = st.text_input("Ad Set ID *", key="adc_adset_id")
        ad_name = st.text_input("Ad Name *", key="adc_name")
        ad_creative_id = st.text_input("Creative ID *", key="adc_creative_id")
    with col_c2:
        ad_status = st.selectbox("Initial Status", ["PAUSED", "ACTIVE"], key="adc_status")
        ad_url_tags = st.text_input("URL Tags (utm params)", key="adc_url_tags")

    if st.button("Create Ad", type="primary", use_container_width=True, key="adc_create"):
        if not ad_adset_id or not ad_name or not ad_creative_id:
            st.error("Ad Set ID, Name, and Creative ID are required.")
        else:
            try:
                result = api.create_ad(
                    adset_id=ad_adset_id,
                    name=ad_name,
                    creative_id=ad_creative_id,
                    status=ad_status,
                )
                st.success(f"Ad created! ID: {result.get('id', 'unknown')}")
            except Exception as e:
                st.error(f"Failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3: AD PREVIEW
# ═══════════════════════════════════════════════════════════════════════════════

with tab_preview:
    st.markdown('<div class="section-title">Ad Preview</div>', unsafe_allow_html=True)

    col_p1, col_p2 = st.columns([3, 2])
    with col_p1:
        preview_ad_id = st.text_input("Ad ID to preview", key="adp_id")
    with col_p2:
        preview_format = st.selectbox("Ad Format", AD_FORMATS, key="adp_format")

    if preview_ad_id and st.button("Generate Preview", type="primary", key="adp_gen"):
        try:
            result = api.get_ad_preview(preview_ad_id, preview_format)
            data = result.get("data", [])
            if data:
                for item in data:
                    body = item.get("body", "")
                    if body:
                        st.markdown(f'<div class="ad-preview">{body}</div>', unsafe_allow_html=True)
            else:
                st.info("No preview available for this ad/format combination.")
        except Exception as e:
            st.error(f"Preview failed: {e}")

    st.markdown("---")
    st.markdown("### Preview by Creative ID")
    col_cp1, col_cp2 = st.columns([3, 2])
    with col_cp1:
        preview_creative_id = st.text_input("Creative ID to preview", key="adpc_id")
    with col_cp2:
        preview_c_format = st.selectbox("Format", AD_FORMATS, key="adpc_format")

    if preview_creative_id and st.button("Preview Creative", type="primary", key="adpc_gen"):
        try:
            result = api.get_creative_preview(preview_creative_id, preview_c_format)
            data = result.get("data", [])
            if data:
                for item in data:
                    body = item.get("body", "")
                    if body:
                        st.markdown(f'<div class="ad-preview">{body}</div>', unsafe_allow_html=True)
            else:
                st.info("No preview available.")
        except Exception as e:
            st.error(f"Preview failed: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4: CREATIVE LIBRARY
# ═══════════════════════════════════════════════════════════════════════════════

with tab_creative:
    st.markdown('<div class="section-title">Creative Library</div>', unsafe_allow_html=True)

    creative_tab1, creative_tab2, creative_tab3, creative_tab4 = st.tabs([
        "All Creatives", "Images", "Videos", "Create Creative",
    ])

    with creative_tab1:
        if st.button("Load Creatives", key="cr_load"):
            try:
                creatives = api.get_creatives()
                if creatives:
                    rows = []
                    for cr in creatives:
                        rows.append({
                            "ID": cr.get("id", ""),
                            "Name": cr.get("name", ""),
                            "Title": cr.get("title", ""),
                            "CTA": cr.get("call_to_action_type", ""),
                            "Image URL": cr.get("image_url", ""),
                            "Link": cr.get("link_url", ""),
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("No creatives found.")
            except Exception as e:
                st.error(f"Failed: {e}")

    with creative_tab2:
        st.markdown("### Ad Images")
        if st.button("Load Images", key="cr_load_img"):
            try:
                images = api.get_ad_images()
                if images:
                    cols = st.columns(4)
                    for i, img in enumerate(images):
                        with cols[i % 4]:
                            url = img.get("url", "")
                            if url:
                                st.image(url, caption=img.get("name", img.get("id", "")), width=150)
                            st.caption(f"ID: {img.get('id', '')}")
                            st.caption(f"{img.get('width', '?')}x{img.get('height', '?')}")
                else:
                    st.info("No images found.")
            except Exception as e:
                st.error(f"Failed: {e}")

        st.markdown("---")
        st.markdown("### Upload Image")
        uploaded_img = st.file_uploader("Upload ad image", type=["png", "jpg", "jpeg"], key="cr_upload_img")
        if uploaded_img and st.button("Upload", key="cr_do_upload_img"):
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp.write(uploaded_img.read())
                tmp_path = tmp.name
            try:
                result = api.upload_image(tmp_path)
                st.success(f"Image uploaded! {result}")
            except Exception as e:
                st.error(f"Upload failed: {e}")
            finally:
                os.unlink(tmp_path)

    with creative_tab3:
        st.markdown("### Ad Videos")
        if st.button("Load Videos", key="cr_load_vid"):
            try:
                videos = api.get_ad_videos()
                if videos:
                    rows = []
                    for v in videos:
                        rows.append({
                            "ID": v.get("id", ""),
                            "Title": v.get("title", ""),
                            "Length": f"{safe_float(v.get('length', 0)):.1f}s",
                            "Created": (v.get("created_time") or "")[:10],
                        })
                    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                else:
                    st.info("No videos found.")
            except Exception as e:
                st.error(f"Failed: {e}")

        st.markdown("---")
        st.markdown("### Upload Video")
        uploaded_vid = st.file_uploader("Upload ad video", type=["mp4", "mov"], key="cr_upload_vid")
        vid_title = st.text_input("Video title", key="cr_vid_title")
        if uploaded_vid and st.button("Upload Video", key="cr_do_upload_vid"):
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(uploaded_vid.read())
                tmp_path = tmp.name
            try:
                result = api.upload_video(tmp_path, title=vid_title)
                st.success(f"Video uploaded! {result}")
            except Exception as e:
                st.error(f"Upload failed: {e}")
            finally:
                os.unlink(tmp_path)

    with creative_tab4:
        st.markdown("### Create Ad Creative")
        cr_name = st.text_input("Creative Name *", key="cr_new_name")
        cr_page_id = st.text_input("Facebook Page ID *", key="cr_page_id")
        cr_message = st.text_area("Post Text", key="cr_message")
        cr_link = st.text_input("Link URL", key="cr_link")
        cr_headline = st.text_input("Headline", key="cr_headline")
        cr_description = st.text_input("Description", key="cr_description")
        cr_image_hash = st.text_input("Image Hash (from uploaded image)", key="cr_img_hash")
        cr_cta = st.selectbox(
            "Call to Action", [
                "LEARN_MORE", "SHOP_NOW", "SIGN_UP", "BOOK_TRAVEL",
                "CONTACT_US", "DOWNLOAD", "GET_OFFER", "GET_QUOTE",
                "SUBSCRIBE", "WATCH_MORE", "APPLY_NOW", "BUY_NOW",
            ], key="cr_cta",
        )

        if st.button("Create Creative", type="primary", use_container_width=True, key="cr_create"):
            if not cr_name or not cr_page_id:
                st.error("Creative name and Page ID are required.")
            else:
                spec = {
                    "page_id": cr_page_id,
                    "link_data": {
                        "message": cr_message,
                        "link": cr_link,
                        "name": cr_headline,
                        "description": cr_description,
                        "call_to_action": {"type": cr_cta},
                    },
                }
                if cr_image_hash:
                    spec["link_data"]["image_hash"] = cr_image_hash
                try:
                    result = api.create_creative(cr_name, spec)
                    st.success(f"Creative created! ID: {result.get('id', 'unknown')}")
                except Exception as e:
                    st.error(f"Failed: {e}")
