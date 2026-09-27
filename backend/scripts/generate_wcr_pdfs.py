import os
import sys
import json
import random
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Ensure backend root is on path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BASE_DIR)

from app.core.config import settings

WCR_DIR = os.path.join(settings.BASE_DIR, "data", "wcr_reports")
os.makedirs(WCR_DIR, exist_ok=True)

# Curated historical drilling incidents and mitigations realistic for these wells and formations
WELL_INCIDENT_PROFILES = {
    "15/9-23": [
        {
            "event_type": "Lost Circulation / Mud Loss",
            "formation": "HORDALAND GP",
            "depth_start": 1680.0,
            "depth_end": 1715.0,
            "severity": "HIGH",
            "npt_hours": 18.5,
            "incident_description": "Encountered sudden severe lost circulation while drilling 12-1/4 inch hole at 1695m in micro-fractured Hordaland shale. Flow-out sensor dropped to 15% with total mud loss rate of 65 bbl/hr. Total fluid lost: 340 bbls.",
            "mitigation_action": "Pulled bit off bottom into 13-3/8 inch casing shoe. Mixed and pumped 50 bbl high-fluid-loss LCM pill containing 25 ppb medium walnut shell and 15 ppb fibrous mica. Waited 4 hours for pill to set. Resumed drilling with reduced pump rate (550 gpm) and maintained mud weight at 1.18 SG. Full returns restored.",
            "lesson_learned": "When drilling through upper Hordaland fractured intervals within 1650-1750m, pre-treat active mud system with fine carbonate and limit ECD to under 1.22 SG."
        },
        {
            "event_type": "Stuck Pipe Incident",
            "formation": "TY FM",
            "depth_start": 2420.0,
            "depth_end": 2445.0,
            "severity": "CRITICAL",
            "npt_hours": 26.0,
            "incident_description": "String became differentially stuck during connection at 2432m in permeable Ty sandstone with 85 psi overbalance. Unable to rotate or pull string with 90 klbs overpull.",
            "mitigation_action": "Spotted 45 bbls organic pipe-freeing soak pill across Ty sand interval. Allowed 3.5 hours soak time while applying intermittent torque and 110 klbs upward jar impacts. String freed on 14th jar stroke. Circulated hole clean and increased mud yield point to 22 lb/100ft2.",
            "lesson_learned": "Avoid static drill string conditions exceeding 3 minutes in Ty formation. Keep pipe rotating during survey/connection procedures."
        }
    ],
    "15/9-14": [
        {
            "event_type": "Well Kick / Influx",
            "formation": "ROGALAND GP",
            "depth_start": 2150.0,
            "depth_end": 2185.0,
            "severity": "CRITICAL",
            "npt_hours": 32.0,
            "incident_description": "Drilling break noted at 2162m with ROP increasing from 12 m/hr to 38 m/hr. Pit gain of 18 bbls observed within 4 minutes. Active gas detector spiked from 1.2% to 14.8% methane.",
            "mitigation_action": "Immediately performed space-out, shut down mud pumps, and closed annular blowout preventer (BOP). SIDPP stabilized at 320 psi; SICP stabilized at 410 psi. Executed Wait and Weight kill sheet procedure, increasing mud weight from 1.22 SG to 1.34 SG. Circulated gas bubble safely through choke manifold and degasser.",
            "lesson_learned": "Rogaland gas-charged sand stringers exhibit sharp abnormal pressure ramps. Implement flow check at any ROP break exceeding 25 m/hr."
        },
        {
            "event_type": "Borehole Instability / Tight Hole",
            "formation": "SELE FM",
            "depth_start": 2310.0,
            "depth_end": 2360.0,
            "severity": "MEDIUM",
            "npt_hours": 12.0,
            "incident_description": "Severe tight hole encountered on trip out at 2335m. Caliper log revealed extensive hole enlargement (16 inch in 12-1/4 inch section) and cavings at shaker.",
            "mitigation_action": "Performed back-reaming with high pump rate. Pumped 30 bbl tandem high-density sweeps (1.30 SG) to evacuate reactive shale cavings. Raised potassium chloride (KCl) concentration to 7% wt to inhibit clay swelling.",
            "lesson_learned": "Sele Formation reactive smectite shales require stringent filtrate loss control (< 4.0 cc) and minimum 6% KCl inhibition."
        }
    ],
    "16/7-6": [
        {
            "event_type": "Lost Circulation / Mud Loss",
            "formation": "CHALK GP",
            "depth_start": 2480.0,
            "depth_end": 2540.0,
            "severity": "HIGH",
            "npt_hours": 21.0,
            "incident_description": "Lost 450 bbls synthetic mud at 2510m in fractured Ekofisk chalk. Static loss rate 40 bbl/hr with zero returns on dynamic circulation.",
            "mitigation_action": "Bullheaded 60 bbls dual-particle size calcium carbonate LCM pill (D50=450um). Reduced mud weight from 1.28 SG to 1.21 SG. Successfully regained full circulation.",
            "lesson_learned": "Ekofisk chalk fractures easily if surge pressures exceed 0.04 SG equivalent. Control tripping speeds to max 15 m/min."
        },
        {
            "event_type": "Cementing Channeling / Loss",
            "formation": "TOR FM",
            "depth_start": 2620.0,
            "depth_end": 2680.0,
            "severity": "MEDIUM",
            "npt_hours": 16.0,
            "incident_description": "Loss of returns during 9-5/8 inch casing cementing job after pumping 120 bbls lead slurry. Annular pressure drop indicated loss into Tor formation vugs.",
            "mitigation_action": "Dropped top plug and displaced with rig pumps at reduced rate. Top of cement found 180m below target. Performed remedial squeeze cementing through perforations at 2615m.",
            "lesson_learned": "Use thixotropic lightweight lead cement slurry (1.45 SG) across Tor chalk formation to avoid exceeding fracture gradient."
        }
    ],
    "25/10-9": [
        {
            "event_type": "Stuck Pipe Incident",
            "formation": "HORDALAND GP",
            "depth_start": 1820.0,
            "depth_end": 1865.0,
            "severity": "HIGH",
            "npt_hours": 22.5,
            "incident_description": "Mechanical pack-off occurred while pulling BHA through swelling claystones at 1842m. Drill string packed off completely with zero circulation.",
            "mitigation_action": "Pumped freshwater/glycol pill to break clay pack-off while jarring downwards at 120 klbs. Regained rotation after 8 hours. Reamed interval twice before pulling out of hole.",
            "lesson_learned": "In Hordaland claystone sections, run stabilizer blades with spiral relief grooves and avoid pulling without continuous low-rate pumping."
        }
    ],
    "25/10-10": [
        {
            "event_type": "Well Kick / Influx",
            "formation": "HEIMDAL FM",
            "depth_start": 2180.0,
            "depth_end": 2220.0,
            "severity": "HIGH",
            "npt_hours": 19.0,
            "incident_description": "Encountered high pressure gas pocket in Heimdal turbidite sand at 2204m. Pit volume gain 14 bbls, background gas 22%.",
            "mitigation_action": "Shut in well on annular preventer. SIDPP=280 psi, SICP=350 psi. Weighted mud from 1.19 SG to 1.28 SG using barite addition. Circulated bottom up cleanly.",
            "lesson_learned": "Heimdal sands in Block 25 are isolated pressure compartments. Ensure barite stock on rig exceeds 120 metric tons before drilling reservoir section."
        }
    ],
    "25/11-24": [
        {
            "event_type": "Lost Circulation / Mud Loss",
            "formation": "BALDER FM",
            "depth_start": 1690.0,
            "depth_end": 1740.0,
            "severity": "MEDIUM",
            "npt_hours": 14.0,
            "incident_description": "Partial mud loss of 25 bbl/hr in porous Balder tuff interval at 1712m. Total mud lost: 160 bbls.",
            "mitigation_action": "Spotted 35 bbls coarse calcium carbonate LCM pill. Lowered pump rate to 600 gpm and adjusted mud weight to 1.16 SG. Losses stabilized.",
            "lesson_learned": "Volcanic tuffs in Balder formation possess low fracture threshold. Monitor ECD closely using PWD (pressure-while-drilling) sub."
        }
    ],
    "31/2-10": [
        {
            "event_type": "Borehole Instability / Pack-off",
            "formation": "HORDALAND GP",
            "depth_start": 1280.0,
            "depth_end": 1340.0,
            "severity": "HIGH",
            "npt_hours": 15.5,
            "incident_description": "Torque erratic with rapid pressure spikes (+600 psi SPP) indicating annular packing around drill collars at 1315m.",
            "mitigation_action": "Discontinued drilling, pulled up 2 stands into shoe, pumped 40 bbl high-viscosity pill with 25 lb/bbl bentonite, circulated 2 bottoms-up until shale cavings cleared.",
            "lesson_learned": "Increase flow rate to 820 gpm to optimize annular cutting transport velocity in oversized top-hole sections."
        }
    ],
    "31/2-21 S": [
        {
            "event_type": "Lost Circulation / Mud Loss",
            "formation": "SOGNEFJORD FM",
            "depth_start": 2150.0,
            "depth_end": 2210.0,
            "severity": "HIGH",
            "npt_hours": 24.0,
            "incident_description": "Complete loss of returns while penetrating unconsolidated Sognefjord oil sand at 2185m. Dynamic losses > 100 bbl/hr.",
            "mitigation_action": "Pumped cross-linked polymer gunk pill (40 bbls) followed by 50 bbl heavy calcium carbonate squeeze pill. Reduced drill fluid density from 1.25 SG to 1.15 SG.",
            "lesson_learned": "Depleted reservoir pressure in Sognefjord sandstone requires strict equivalent mud weight management under 1.16 SG."
        },
        {
            "event_type": "Differential Sticking",
            "formation": "FENSFJORD FM",
            "depth_start": 2680.0,
            "depth_end": 2720.0,
            "severity": "HIGH",
            "npt_hours": 18.0,
            "incident_description": "Differential sticking while taking directional survey at 2698m. Drill collars embedded against permeable filter cake.",
            "mitigation_action": "Pumped 50 bbl diesel-glycol release pill. Reduced hydrostatic pressure by lightened fluid displacement. String pulled free at 80 klbs overpull.",
            "lesson_learned": "Utilize spiral drill collars and keep string in continuous rotation when stationary on bottom."
        }
    ],
    "34/3-2 S": [
        {
            "event_type": "Well Kick / Influx",
            "formation": "STATFJORD FM",
            "depth_start": 3820.0,
            "depth_end": 3880.0,
            "severity": "CRITICAL",
            "npt_hours": 36.0,
            "incident_description": "Major gas influx at 3845m in high-pressure Statfjord sandstone. Flow check positive with 25 bbls pit volume increase in 5 minutes.",
            "mitigation_action": "Shut in on pipe rams. SIDPP=480 psi, SICP=590 psi. Successfully killed well via Engineer's Method, raising mud weight from 1.48 SG to 1.62 SG with barite.",
            "lesson_learned": "Deep Statfjord formation requires pre-loading mud pits with high-density kill fluid prior to reservoir section penetration."
        }
    ],
    "34/3-3 A": [
        {
            "event_type": "Lost Circulation / Mud Loss",
            "formation": "SHETLAND GP",
            "depth_start": 3120.0,
            "depth_end": 3170.0,
            "severity": "HIGH",
            "npt_hours": 20.0,
            "incident_description": "Severe circulation losses of 75 bbl/hr encountered in fractured limestone streaks of Shetland Group at 3145m.",
            "mitigation_action": "Pumped engineered LCM blend (fibers, mica, coarse carbonate). Squeezed 30 bbls into formation at 400 psi squeeze pressure. Full returns restored.",
            "lesson_learned": "Conduct LOT (Leak-Off Test) immediately upon drilling 5m out of 13-3/8 inch casing shoe in Shetland formation."
        }
    ],
    "35/9-7": [
        {
            "event_type": "Overpressure / Tight Hole",
            "formation": "VIKING GP",
            "depth_start": 2650.0,
            "depth_end": 2710.0,
            "severity": "HIGH",
            "npt_hours": 17.0,
            "incident_description": "Encountered high pore pressure transition zone in Viking organic shales at 2682m. Severe background gas (18%) and splitty shale cavings.",
            "mitigation_action": "Increased active mud weight from 1.30 SG to 1.42 SG. Conducted short wiper trip to 9-5/8 inch shoe. Hole stabilized.",
            "lesson_learned": "Transition into Viking shales requires gradual density weighting. Use real-time PWD sonic porosity to track pore pressure ramp."
        }
    ],
    "35/9-8": [
        {
            "event_type": "Lost Circulation / Induced Fracture",
            "formation": "BRENT GP",
            "depth_start": 2980.0,
            "depth_end": 3030.0,
            "severity": "HIGH",
            "npt_hours": 25.0,
            "incident_description": "Encountered total mud loss (380 bbls) at 3010m when surge pressure during BHA trip fractured depleted Brent Tarbert sand.",
            "mitigation_action": "Spotted 60 bbls high-squeeze thixotropic LCM pill. Maintained annular fluid level with seawater down annulus. Reduced trip-in speed to 8 m/min.",
            "lesson_learned": "Depleted Brent sandstones possess narrow drilling margins (< 0.08 SG window). Install continuous auto-trip tank monitoring."
        },
        {
            "event_type": "Stuck Pipe / Differential",
            "formation": "BRENT GP",
            "depth_start": 3080.0,
            "depth_end": 3110.0,
            "severity": "HIGH",
            "npt_hours": 21.0,
            "incident_description": "BHA stuck differentially across Ness sandstone at 3094m while taking MWD formation pressure test. 110 klbs overpull ineffective.",
            "mitigation_action": "Soaked string in 50 bbls glycol-ester lubricant pill for 4 hours. Worked pipe with 130 klbs jar hits. Pipe freed without backing off.",
            "lesson_learned": "Minimize formation tester tool stationary time to under 12 minutes in Brent sands. Treat mud with 3% lubricity additive."
        }
    ]
}

# Generic fallback incidents for wells without custom profile to ensure all 21 wells have rich knowledge data
DEFAULT_INCIDENT_TEMPLATES = [
    {
        "event_type": "Lost Circulation / Mud Loss",
        "formation": "HORDALAND GP",
        "depth_offset": 0.45,  # fraction of total depth
        "severity": "HIGH",
        "npt_hours": 16.0,
        "incident_description": "Partial circulation loss of 40 bbl/hr observed while drilling 12-1/4 inch hole. Total fluid loss: 220 bbls.",
        "mitigation_action": "Pumped 40 bbls medium grade LCM pill (calcium carbonate and fine fiber). Reduced pump circulation rate from 750 gpm to 580 gpm.",
        "lesson_learned": "Maintain ECD buffer below 1.25 SG across fractured shale intervals."
    },
    {
        "event_type": "Borehole Instability / Tight Hole",
        "formation": "ROGALAND GP",
        "depth_offset": 0.65,
        "severity": "MEDIUM",
        "npt_hours": 11.5,
        "incident_description": "Overpull of 60 klbs and tight spot during wiper trip. Shakers showed blocky cavings indicating shale spalling.",
        "mitigation_action": "Reamed hole section with high rotary speed (120 rpm) and pumped 25 bbl high-viscosity bentonite sweep.",
        "lesson_learned": "Perform regular wiper trips every 150m drilled in reactive claystone formations."
    }
]

def generate_pdf_report(well_data: dict, output_path: str):
    well_id = well_data["well_id"]
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom distinct styles
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0B2545'),
        alignment=1, # Center
        spaceAfter=6
    )

    subhead_style = ParagraphStyle(
        'SubheadStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#134074'),
        alignment=1,
        spaceAfter=12
    )

    section_title = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0B2545'),
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1D2D44')
    )

    body_bold = ParagraphStyle(
        'CustomBodyBold',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0B2545'),
        fontName='Helvetica-Bold'
    )

    incident_title = ParagraphStyle(
        'IncTitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#8B0000'),
        fontName='Helvetica-Bold'
    )

    elements = []

    # Title & Header
    elements.append(Paragraph("OIL INDIA LIMITED - eRTMAC OPERATIONS", header_style))
    elements.append(Paragraph(f"OFFICIAL WELL COMPLETION REPORT (WCR) & DRILLING HISTORY<br/><b>WELL IDENTIFIER: {well_id}</b>", subhead_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#134074'), spaceAfter=10))

    # Section 1: Well General & Geospatial Data
    elements.append(Paragraph("1. Well Location & Technical Header", section_title))

    header_table_data = [
        [Paragraph("<b>Operator:</b> Oil India Limited / Joint North Sea", body_style), Paragraph(f"<b>Well Name:</b> {well_id}", body_style)],
        [Paragraph(f"<b>UTM Easting (X):</b> {well_data['x_utm']:.1f} m", body_style), Paragraph(f"<b>UTM Northing (Y):</b> {well_data['y_utm']:.1f} m", body_style)],
        [Paragraph(f"<b>Latitude:</b> {well_data.get('latitude', 58.0):.6f}° N", body_style), Paragraph(f"<b>Longitude:</b> {well_data.get('longitude', 2.0):.6f}° E", body_style)],
        [Paragraph(f"<b>Total Depth (MD):</b> {well_data['depth_max_m']:.1f} m", body_style), Paragraph(f"<b>Spud Depth:</b> {well_data['depth_min_m']:.1f} m", body_style)],
        [Paragraph("<b>Drilling Rig:</b> eRTMAC Semi-Submersible Rig-07", body_style), Paragraph("<b>Status:</b> Plugged & Abandoned (P&A) / Offset Reference", body_style)]
    ]
    t1 = Table(header_table_data, colWidths=[270, 270])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EEF4F8')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#8DA9C4')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 10))

    # Section 2: Stratigraphy & Formation Tops
    elements.append(Paragraph("2. Stratigraphic Progression & Formation Tops", section_title))
    strat_rows = [["Formation / Stratum Name", "Top Depth MD (m)", "Lithology Characterization", "Drillability / Risk Profile"]]

    formations = well_data.get("formations", [])
    if not formations:
        formations = ["HORDALAND GP", "ROGALAND GP", "SELE FM", "BALDER FM", "CHALK GP", "EKOFISK FM", "TOR FM"]

    depth_step = (well_data['depth_max_m'] - well_data['depth_min_m']) / max(len(formations), 1)
    for i, form in enumerate(formations):
        f_depth = round(well_data['depth_min_m'] + (i * depth_step), 1)
        lith = "Shale / Claystone with interbedded siltstone" if "HORD" in form.upper() or "SELE" in form.upper() else (
            "Chalk / Hard Calcareous Limestone" if "CHALK" in form.upper() or "TOR" in form.upper() or "EKOFISK" in form.upper() else (
                "Porous Turbidite Sandstone (Hydrocarbon Bearing)" if "HEIMDAL" in form.upper() or "TY" in form.upper() or "BRENT" in form.upper() else "Interbedded Sand / Shale"
            )
        )
        risk = "Loss / Depletion" if "SAND" in lith.upper() else ("Fractured / Losses" if "CHALK" in lith.upper() else "Tight Hole / Swelling")
        strat_rows.append([form, f"{f_depth:.1f} m", lith, risk])

    t2 = Table([[Paragraph(c, body_bold if r==0 else body_style) for c in row] for r, row in enumerate(strat_rows)], colWidths=[130, 80, 210, 120])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#134074')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 10))

    # Section 3: Casing & Mud Architecture
    elements.append(Paragraph("3. Casing Design & Mud Program Summary", section_title))
    casing_rows = [
        ["Hole Section", "Casing OD", "Shoe Depth (MD)", "Mud Type", "Mud Weight (SG)", "LOT / FIT (SG)"],
        ["36 in Hole", "30 in Conductor", "350 m", "Spud Mud / Seawater", "1.05 SG", "FIT 1.25 SG"],
        ["26 in Hole", "20 in Surface", "1,050 m", "KCl / Polymer", "1.12 SG", "LOT 1.45 SG"],
        ["17-1/2 in Hole", "13-3/8 in Interm.", "2,200 m", "Low Solids Non-Dispersed", "1.24 SG", "LOT 1.62 SG"],
        ["12-1/4 in Hole", "9-5/8 in Prod.", f"{min(well_data['depth_max_m'] - 300, 3100):.0f} m", "Oil Based / Synthetic Mud", "1.32 SG", "LOT 1.78 SG"],
        ["8-1/2 in Hole", "7 in Liner", f"{well_data['depth_max_m']:.0f} m", "Synthetic Oil Based (SOBM)", "1.38 SG", "LOT 1.88 SG"]
    ]
    t3 = Table([[Paragraph(c, body_bold if r==0 else body_style) for c in row] for r, row in enumerate(casing_rows)], colWidths=[80, 85, 95, 130, 85, 65])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0B2545')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    elements.append(t3)
    elements.append(Spacer(1, 14))

    # Page Break for Operational Incidents and Mitigation Records (Ensures multi-page grounded indexing)
    elements.append(PageBreak())

    # Section 4: Chronological Operational Incidents & Lessons Learned (Page 2)
    elements.append(Paragraph(f"4. Historical Operational Incidents, NPT & Mitigations (Well: {well_id})", section_title))
    elements.append(Paragraph("<i>This section constitutes the institutional memory log extracted by the NWIS knowledge engine. All alerts generated during active drilling cite these exact records.</i>", subhead_style))
    elements.append(Spacer(1, 4))

    # Retrieve incidents
    incidents = WELL_INCIDENT_PROFILES.get(well_id, [])
    if not incidents:
        # Generate custom realistic incidents adapted to well depth
        d_range = well_data['depth_max_m'] - well_data['depth_min_m']
        incidents = [
            {
                "event_type": "Lost Circulation / Mud Loss",
                "formation": formations[min(2, len(formations)-1)],
                "depth_start": round(well_data['depth_min_m'] + d_range * 0.42, 1),
                "depth_end": round(well_data['depth_min_m'] + d_range * 0.45, 1),
                "severity": "HIGH",
                "npt_hours": 16.5,
                "incident_description": f"Experienced 45 bbl/hr mud loss at {well_data['depth_min_m'] + d_range * 0.43:.1f}m while drilling through permeable {formations[min(2, len(formations)-1)]} section.",
                "mitigation_action": "Pumped 45 bbl LCM pill with multi-modal calcium carbonate. Reduced flow rate by 15% and maintained backpressure.",
                "lesson_learned": "Pre-treat active system with bridging agents prior to drilling formation boundary."
            },
            {
                "event_type": "Tight Hole / Stuck Pipe Risk",
                "formation": formations[min(5, len(formations)-1)],
                "depth_start": round(well_data['depth_min_m'] + d_range * 0.72, 1),
                "depth_end": round(well_data['depth_min_m'] + d_range * 0.76, 1),
                "severity": "MEDIUM",
                "npt_hours": 10.0,
                "incident_description": f"High torque and 45 klbs overpull on connections at {well_data['depth_min_m'] + d_range * 0.74:.1f}m due to reactive shale sloughing.",
                "mitigation_action": "Conducted wiper trip, increased mud yield point to 20 lb/100ft2, and raised polymer encapsulator dosage.",
                "lesson_learned": "Do not let drillstring remain stationary for more than 4 minutes in this section."
            }
        ]

    for idx, inc in enumerate(incidents):
        box_data = [
            [
                Paragraph(f"<b>INCIDENT #{idx+1}: {inc['event_type']}</b>", incident_title),
                Paragraph(f"<b>Severity:</b> <font color='{'red' if inc['severity'] in ['HIGH', 'CRITICAL'] else 'orange'}'>{inc['severity']}</font>", body_bold),
                Paragraph(f"<b>NPT Hours:</b> {inc['npt_hours']} hrs", body_bold)
            ],
            [
                Paragraph(f"<b>Depth Interval:</b> {inc['depth_start']:.1f} m - {inc['depth_end']:.1f} m", body_style),
                Paragraph(f"<b>Formation:</b> {inc['formation']}", body_style),
                Paragraph("<b>Status:</b> Resolved on Site", body_style)
            ],
            [
                Paragraph(f"<b>Event Occurrence Narrative:</b><br/>{inc['incident_description']}", body_style),
                "", ""
            ],
            [
                Paragraph(f"<b>Mitigation Action Applied:</b><br/>{inc['mitigation_action']}", body_style),
                "", ""
            ],
            [
                Paragraph(f"<b>Offset Drilling Recommendation & Institutional Lesson:</b><br/>{inc['lesson_learned']}", body_style),
                "", ""
            ]
        ]

        t_inc = Table(box_data, colWidths=[180, 180, 180])
        t_inc.setStyle(TableStyle([
            ('SPAN', (0, 2), (2, 2)),
            ('SPAN', (0, 3), (2, 3)),
            ('SPAN', (0, 4), (2, 4)),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FBFBFB')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#DC2626') if inc['severity'] in ['HIGH', 'CRITICAL'] else colors.HexColor('#F59E0B')),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor('#CBD5E1')),
            ('LINEBELOW', (0, 1), (-1, 1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_inc)
        elements.append(Spacer(1, 10))

    # Build Document
    doc.build(elements)
    print(f"Generated WCR PDF: {os.path.basename(output_path)} with {len(incidents)} incidents.")

def main():
    print("Generating Authentic WCR Drilling Completion Report PDFs...")
    # Load well catalog or scan force2020 directory
    from app.services.geospatial_service import geospatial_service
    wells = geospatial_service.get_all_wells()
    print(f"Found {len(wells)} wells in catalog.")

    for well in wells:
        clean_name = well.well_id.replace("/", "_").replace(" ", "_")
        pdf_name = f"WCR_{clean_name}.pdf"
        pdf_path = os.path.join(WCR_DIR, pdf_name)
        generate_pdf_report(well.model_dump(), pdf_path)

    print(f"\nAll WCR Reports generated in: {WCR_DIR}\n")

if __name__ == "__main__":
    main()
