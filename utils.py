# utils.py
import math
from itsdangerous import URLSafeTimedSerializer

def haversine_km(lat1, lon1, lat2, lon2):
    # guard
    if None in (lat1, lon1, lat2, lon2):
        return None
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlmb/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def make_token(secret_key, payload, salt):
    s = URLSafeTimedSerializer(secret_key)
    return s.dumps(payload, salt=salt)

def read_token(secret_key, token, salt, max_age_seconds):
    s = URLSafeTimedSerializer(secret_key)
    return s.loads(token, salt=salt, max_age=max_age_seconds)
