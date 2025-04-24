from streamlit_webrtc import webrtc_streamer, WebRtcMode
import streamlit as st

def audio_recorder(key: str):
    return webrtc_streamer(
        key=key,
        mode=WebRtcMode.SENDONLY,
        audio_receiver_size=1024,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        media_stream_constraints={"audio": True, "video": False}
    )