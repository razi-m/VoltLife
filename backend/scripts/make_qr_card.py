import sys
import os

# Adjust path to import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.aadhaar import decode_bpan

def generate_hero_card_html(aadhaar_id: str, output_path: str = "hero_card.html"):
    """
    Parses the 21-character BPAN Aadhaar ID and generates a beautiful, printable
    HTML passport card with a QR code.
    """
    try:
        decoded = decode_bpan(aadhaar_id)
    except Exception as e:
        print(f"Error decoding Aadhaar ID: {e}")
        return

    qr_target_url = f"https://voltlife.railway.app/api/v1/aadhaar/{aadhaar_id}"
    qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=160x160&data={qr_target_url}"

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>VoltLife Battery Aadhaar Card</title>
    <style>
        body {{
            font-family: 'Inter', system-ui, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }}
        .card {{
            width: 450px;
            background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
            border: 2px solid #30363d;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            position: relative;
            overflow: hidden;
        }}
        .card::before {{
            content: "";
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(56, 189, 248, 0.05) 0%, transparent 70%);
            pointer-events: none;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #30363d;
            padding-bottom: 16px;
            margin-bottom: 20px;
        }}
        .title {{
            font-size: 20px;
            font-weight: 700;
            color: #38bdf8;
            letter-spacing: 1px;
        }}
        .badge {{
            background: rgba(56, 189, 248, 0.1);
            color: #38bdf8;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid rgba(56, 189, 248, 0.2);
        }}
        .content-area {{
            display: flex;
            gap: 20px;
        }}
        .details {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .detail-row {{
            display: flex;
            flex-direction: column;
        }}
        .label {{
            font-size: 11px;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .value {{
            font-size: 14px;
            color: #f0f6fc;
            font-weight: 600;
        }}
        .qr-area {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 8px;
        }}
        .qr-frame {{
            background: white;
            padding: 8px;
            border-radius: 8px;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .qr-label {{
            font-size: 9px;
            color: #8b949e;
            text-align: center;
        }}
        .footer {{
            margin-top: 24px;
            font-size: 10px;
            color: #8b949e;
            text-align: center;
            border-top: 1px solid #30363d;
            padding-top: 12px;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <div class="title">BATTERY AADHAAR</div>
            <div class="badge">MoRTH Draft COMPLIANT</div>
        </div>
        <div class="content-area">
            <div class="details">
                <div class="detail-row">
                    <span class="label">Aadhaar Number</span>
                    <span class="value" style="font-family: monospace; color: #38bdf8;">{aadhaar_id}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Manufacturer</span>
                    <span class="value">{decoded['manufacturer']}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Chemistry / Cells</span>
                    <span class="value">{decoded['chemistry']} ({decoded['voltage']} Nominal)</span>
                </div>
                <div class="detail-row">
                    <span class="label">Rated Capacity</span>
                    <span class="value">{decoded['capacity_kwh']:.1f} kWh</span>
                </div>
                <div class="detail-row">
                    <span class="label">Birthdate</span>
                    <span class="value">{decoded['manufactured'].strftime('%Y-%m-%d')}</span>
                </div>
                <div class="detail-row">
                    <span class="label">Serial Code</span>
                    <span class="value">{decoded['serial']}</span>
                </div>
            </div>
            <div class="qr-area">
                <div class="qr-frame">
                    <img src="{qr_api_url}" alt="Passport QR" width="140" height="140">
                </div>
                <span class="qr-label">Scan to verify<br>lifecycle history</span>
            </div>
        </div>
        <div class="footer">
            VoltLife Battery Lifecycle Operating System • India 2030
        </div>
    </div>
</body>
</html>
"""
    with open(output_path, "w") as f:
        f.write(html_content)
    print(f"Printable card successfully generated and saved to {output_path}")

if __name__ == "__main__":
    aadhaar = "INFOAN480415032400231"
    if len(sys.argv) > 1:
        aadhaar = sys.argv[1]
    generate_hero_card_html(aadhaar)
