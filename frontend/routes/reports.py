"""
Reports routes - CSV and PDF generation
"""
from flask import Blueprint, render_template, request, current_app, make_response
import requests
import csv
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/')
def reports_home():
    """Reports homepage"""
    api_url = current_app.config['API_BASE_URL']

    try:
        provinces = requests.get(f"{api_url}/provinces/").json()
        districts = requests.get(f"{api_url}/districts/").json()
        constituencies = requests.get(f"{api_url}/constituencies/").json()
        wards = requests.get(f"{api_url}/wards/").json()
    except:
        provinces, districts, constituencies, wards = [], [], [], []

    return render_template('reports/index.html',
                         provinces=provinces,
                         districts=districts,
                         constituencies=constituencies,
                         wards=wards)


@reports_bp.route('/generate/csv')
def generate_csv():
    """Generate CSV report"""
    api_url = current_app.config['API_BASE_URL']

    # Get filter parameters
    province_id = request.args.get('province_id')
    district_id = request.args.get('district_id')
    constituency_id = request.args.get('constituency_id')
    ward_id = request.args.get('ward_id')
    gender = request.args.get('gender')

    # Fetch members
    try:
        members = requests.get(f"{api_url}/members/").json()
        provinces = requests.get(f"{api_url}/provinces/").json()
        districts = requests.get(f"{api_url}/districts/").json()
        constituencies = requests.get(f"{api_url}/constituencies/").json()
        wards = requests.get(f"{api_url}/wards/").json()
    except:
        members = []
        provinces, districts, constituencies, wards = [], [], [], []

    # Create lookup dictionaries
    province_map = {p['id']: p['name'] for p in provinces}
    district_map = {d['id']: {'name': d['name'], 'province_id': d['province_id']} for d in districts}
    constituency_map = {c['id']: {'name': c['name'], 'district_id': c['district_id']} for c in constituencies}
    ward_map = {w['id']: {'name': w['name'], 'constituency_id': w['constituency_id']} for w in wards}

    # Filter members
    filtered_members = []
    for member in members:
        # Get location hierarchy
        if member.get('ward_id') and member['ward_id'] in ward_map:
            ward_info = ward_map[member['ward_id']]
            const_id = ward_info['constituency_id']
            const_info = constituency_map.get(const_id, {})
            dist_id = const_info.get('district_id')
            dist_info = district_map.get(dist_id, {})
            prov_id = dist_info.get('province_id')

            # Apply filters
            if ward_id and str(member['ward_id']) != str(ward_id):
                continue
            if constituency_id and str(const_id) != str(constituency_id):
                continue
            if district_id and str(dist_id) != str(district_id):
                continue
            if province_id and str(prov_id) != str(province_id):
                continue
            if gender and member.get('gender') != gender:
                continue

            # Add location info to member
            member['province_name'] = province_map.get(prov_id, 'N/A')
            member['district_name'] = dist_info.get('name', 'N/A')
            member['constituency_name'] = const_info.get('name', 'N/A')
            member['ward_name'] = ward_info.get('name', 'N/A')

            filtered_members.append(member)

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'ID', 'Name', 'Gender', 'Age', 'NRC', 'Voters ID', 'Contact',
        'Province', 'District', 'Constituency', 'Ward', 'Registered Date'
    ])

    # Write data
    for member in filtered_members:
        writer.writerow([
            member.get('id', ''),
            member.get('name', ''),
            member.get('gender', ''),
            member.get('age', ''),
            member.get('nrc', ''),
            member.get('voters_id', ''),
            member.get('contact', ''),
            member.get('province_name', ''),
            member.get('district_name', ''),
            member.get('constituency_name', ''),
            member.get('ward_name', ''),
            member.get('created_at', '').split('T')[0] if member.get('created_at') else ''
        ])

    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=member_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    return response


@reports_bp.route('/generate/pdf')
def generate_pdf():
    """Generate PDF report"""
    api_url = current_app.config['API_BASE_URL']

    # Get filter parameters
    province_id = request.args.get('province_id')
    district_id = request.args.get('district_id')
    constituency_id = request.args.get('constituency_id')
    ward_id = request.args.get('ward_id')
    gender = request.args.get('gender')

    # Fetch members
    try:
        members = requests.get(f"{api_url}/members/").json()
        provinces = requests.get(f"{api_url}/provinces/").json()
        districts = requests.get(f"{api_url}/districts/").json()
        constituencies = requests.get(f"{api_url}/constituencies/").json()
        wards = requests.get(f"{api_url}/wards/").json()
    except:
        members = []
        provinces, districts, constituencies, wards = [], [], [], []

    # Create lookup dictionaries
    province_map = {p['id']: p['name'] for p in provinces}
    district_map = {d['id']: {'name': d['name'], 'province_id': d['province_id']} for d in districts}
    constituency_map = {c['id']: {'name': c['name'], 'district_id': c['district_id']} for c in constituencies}
    ward_map = {w['id']: {'name': w['name'], 'constituency_id': w['constituency_id']} for w in wards}

    # Filter members
    filtered_members = []
    for member in members:
        # Get location hierarchy
        if member.get('ward_id') and member['ward_id'] in ward_map:
            ward_info = ward_map[member['ward_id']]
            const_id = ward_info['constituency_id']
            const_info = constituency_map.get(const_id, {})
            dist_id = const_info.get('district_id')
            dist_info = district_map.get(dist_id, {})
            prov_id = dist_info.get('province_id')

            # Apply filters
            if ward_id and str(member['ward_id']) != str(ward_id):
                continue
            if constituency_id and str(const_id) != str(constituency_id):
                continue
            if district_id and str(dist_id) != str(district_id):
                continue
            if province_id and str(prov_id) != str(province_id):
                continue
            if gender and member.get('gender') != gender:
                continue

            # Add location info to member
            member['province_name'] = province_map.get(prov_id, 'N/A')
            member['district_name'] = dist_info.get('name', 'N/A')
            member['constituency_name'] = const_info.get('name', 'N/A')
            member['ward_name'] = ward_info.get('name', 'N/A')

            filtered_members.append(member)

    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)

    # Container for PDF elements
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=12,
        alignment=1  # Center
    )

    # Title
    title = Paragraph("Member Registry Report", title_style)
    elements.append(title)

    # Report info
    info_style = styles['Normal']
    info_text = f"Generated on: {datetime.now().strftime('%B %d, %Y at %H:%M')}<br/>"
    info_text += f"Total Members: {len(filtered_members)}"
    info = Paragraph(info_text, info_style)
    elements.append(info)
    elements.append(Spacer(1, 0.3*inch))

    # Table data
    data = [['ID', 'Name', 'Gender', 'Age', 'NRC', 'Province', 'District', 'Constituency']]

    for member in filtered_members:
        data.append([
            str(member.get('id', '')),
            member.get('name', '')[:20],  # Truncate long names
            member.get('gender', ''),
            str(member.get('age', '')),
            member.get('nrc', '')[:15],
            member.get('province_name', '')[:12],
            member.get('district_name', '')[:12],
            member.get('constituency_name', '')[:15]
        ])

    # Create table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))

    elements.append(table)

    # Build PDF
    doc.build(elements)

    # Create response
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=member_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'

    return response
