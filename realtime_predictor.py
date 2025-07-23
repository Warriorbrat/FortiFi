import os
import sys
import django
import joblib
import pandas as pd
import numpy as np
from scapy.all import sniff, IP, TCP, UDP, Raw, conf
import warnings


warnings.filterwarnings("ignore")

# === Django Setup for Database Logging ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nids.settings")
django.setup()

from core.models import RealTimeLog  # Import RealTimeLog model

# === Load Trained Model & Feature Columns ===
print("📦 Loading trained model...")

model_path = r"C:\Users\himur\OneDrive\Desktop\nids_project\model\trained_model.pkl"

if not os.path.exists(model_path):
    print(f"❌ Model file not found at: {model_path}")
    sys.exit()

try:
    model, feature_columns = joblib.load(model_path)
    print(f"✅ Model loaded successfully! Total features: {len(feature_columns)}")
except Exception as e:
    print(f"⚠️ Error loading model: {e}")
    sys.exit()

# === Feature Extraction from Packet ===
def extract_features_from_packet(packet):
    """Extracts required features from a network packet."""
    
    feature_dict = {col: 0.0 for col in feature_columns}  # Initialize all features to 0

    try:
        if IP in packet:
            ip_layer = packet[IP]

            # === Basic Features ===
            feature_dict[' Destination Port'] = ip_layer.dport if hasattr(ip_layer, 'dport') else 0
            feature_dict[' Flow Duration'] = 0  # Placeholder since duration is per-flow
            feature_dict['Total Fwd Packets'] = 1
            feature_dict['Total Backward Packets'] = 1
            feature_dict['Total Length of Fwd Packets'] = len(packet)
            feature_dict['Total Length of Bwd Packets'] = len(packet)
            feature_dict['Fwd Packet Length Max'] = len(packet)
            feature_dict['Fwd Packet Length Min'] = len(packet)
            feature_dict['Fwd Packet Length Mean'] = len(packet)
            feature_dict['Fwd Packet Length Std'] = 0  # Placeholder
            feature_dict['Bwd Packet Length Max'] = len(packet)
            feature_dict['Bwd Packet Length Min'] = len(packet)
            feature_dict['Bwd Packet Length Mean'] = len(packet)
            feature_dict['Bwd Packet Length Std'] = 0
            feature_dict[' Flow Packets/s'] = 1
            feature_dict[' Flow Bytes/s'] = len(packet)
            feature_dict['Fwd Header Length'] = len(ip_layer.payload)
            feature_dict['Bwd Header Length'] = len(ip_layer.payload)

            # === Advanced Features ===
            feature_dict['Flow IAT Mean'] = 0
            feature_dict['Flow IAT Std'] = 0
            feature_dict['Flow IAT Max'] = 0
            feature_dict['Flow IAT Min'] = 0
            feature_dict['Fwd IAT Total'] = 0
            feature_dict['Fwd IAT Mean'] = 0
            feature_dict['Fwd IAT Std'] = 0
            feature_dict['Fwd IAT Max'] = 0
            feature_dict['Fwd IAT Min'] = 0
            feature_dict['Bwd IAT Total'] = 0
            feature_dict['Bwd IAT Mean'] = 0
            feature_dict['Bwd IAT Std'] = 0
            feature_dict['Bwd IAT Max'] = 0
            feature_dict['Bwd IAT Min'] = 0
            feature_dict['Fwd PSH Flags'] = 1 if TCP in packet and packet[TCP].flags & 0x08 else 0
            feature_dict['Bwd PSH Flags'] = 1 if TCP in packet and packet[TCP].flags & 0x08 else 0
            feature_dict['Fwd URG Flags'] = 1 if TCP in packet and packet[TCP].flags & 0x20 else 0
            feature_dict['Bwd URG Flags'] = 1 if TCP in packet and packet[TCP].flags & 0x20 else 0
            feature_dict['Fwd Packets/s'] = 1
            feature_dict['Bwd Packets/s'] = 1
            feature_dict['Min Packet Length'] = len(packet)
            feature_dict['Max Packet Length'] = len(packet)
            feature_dict['Packet Length Mean'] = len(packet)
            feature_dict['Packet Length Std'] = 0
            feature_dict['Packet Length Variance'] = 0

            # === Flag Counts ===
            feature_dict['FIN Flag Count'] = 1 if TCP in packet and packet[TCP].flags & 0x01 else 0
            feature_dict['SYN Flag Count'] = 1 if TCP in packet and packet[TCP].flags & 0x02 else 0
            feature_dict['RST Flag Count'] = 1 if TCP in packet and packet[TCP].flags & 0x04 else 0
            feature_dict['PSH Flag Count'] = 1 if TCP in packet and packet[TCP].flags & 0x08 else 0
            feature_dict['ACK Flag Count'] = 1 if TCP in packet and packet[TCP].flags & 0x10 else 0
            feature_dict['URG Flag Count'] = 1 if TCP in packet and packet[TCP].flags & 0x20 else 0

    except Exception as e:
        print(f"⚠️ Error extracting features: {e}")

    # Convert to DataFrame and align order
    feature_df = pd.DataFrame([feature_dict])[feature_columns]
    
    # Replace infinities and NaNs
    feature_df.replace([np.inf, -np.inf], 0, inplace=True)
    feature_df.fillna(0, inplace=True)

    return feature_df

# === Packet Prediction Function ===
def predict_packet(packet):
    features = extract_features_from_packet(packet)

    try:
        prediction = model.predict(features)[0]
        print(f"📡 Packet Prediction: {prediction}")

        # Store prediction in database
        RealTimeLog.objects.create(
            src_ip=packet[IP].src if IP in packet else None,
            dst_ip=packet[IP].dst if IP in packet else None,
            protocol=packet[IP].proto if IP in packet else "Unknown",
            prediction=prediction
        )

    except Exception as e:
        print(f"⚠️ Prediction error: {e}")

# === Start Packet Sniffing ===
print("🚀 Starting Real-Time Packet Sniffing & Prediction...")

try:
    # Try Layer 2 sniffing (requires WinPcap/Npcap)
    sniff(prn=predict_packet, store=0)
except Exception as e:
    print("⚠️ Layer 2 sniffing failed. Falling back to Layer 3...")
    try:
        sniff(prn=predict_packet, store=0, iface=conf.iface, socket=conf.L3socket)
    except Exception as e2:
        print(f"❌ Layer 3 fallback failed: {e2}")
